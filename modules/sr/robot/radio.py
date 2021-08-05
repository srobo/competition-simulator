from __future__ import annotations

import struct
from math import atan2
from typing import List, Optional, NamedTuple
from threading import Lock

from controller import Robot, Receiver
from shared_utils import Owner, TargetInfo, TargetType
from sr.robot.utils import get_robot_device
from sr.robot.coordinates import Vector

# Updating? Update territory_controller.py too.
BROADCASTS_PER_SECOND = 10


def parse_radio_message(message: bytes, zone: int) -> Optional[TargetInfo]:
    try:
        token_type, token_code, owner = struct.unpack("!bBb", message)
        return TargetInfo(
            type=TargetType(token_type),
            owner=Owner(owner),
            id=token_code,
        )
    except ValueError:
        print(f"Robot starting in zone {zone} received malformed message.")  # noqa:T001
        return None


class Target(NamedTuple):
    """
    A snapshot of information about a radio target.
    """
    bearing: float
    signal_strength: float
    target_info: TargetInfo

    @classmethod
    def from_vector(
        cls,
        signal_strength: float,
        target_info: TargetInfo,
        vector: Vector,
    ) -> Target:
        x, _, z = vector.data  # 2-dimensional bearing in the xz plane, elevation is ignored
        # Webots uses z-forward orientation for the bearing but the default receiver
        # orientation is x-forward so this converts that to (-pi, pi) with 0 facing forward
        bearing = -atan2(x, z)
        return cls(bearing=bearing, signal_strength=signal_strength, target_info=target_info)

    def __repr__(self) -> str:
        return '<{}: {}>'.format(type(self).__name__, ', '.join((
            f'info={self.target_info}',
            f'bearing={self.bearing}',
            f'strength={self.signal_strength}',
        )))


class Radio:
    """
    Wraps a radio target and reciever unit on the Robot.
    """

    def __init__(self, webot: Robot, zone: int, step_lock: Lock) -> None:
        self._webot = webot
        self._receiver = get_robot_device(webot, "robot receiver", Receiver)
        self._receiver.enable(1)
        self._zone = zone
        self._step_lock = step_lock

    def sweep(self) -> List[Target]:
        """
        Sweep for nearby radio targets.

        Sweeping takes 0.1 seconds
        """
        receiver = self._receiver
        # Clear the buffer
        while receiver.getQueueLength():
            receiver.nextPacket()
        # Wait 1 sweep
        with self._step_lock:
            self._webot.step(int(max(1, 1000 // BROADCASTS_PER_SECOND)))
        # Read the buffer
        targets = []
        while receiver.getQueueLength():
            try:
                info = parse_radio_message(receiver.getData(), self._zone)
                if info is not None:
                    targets.append(
                        Target.from_vector(
                            vector=Vector(receiver.getEmitterDirection()),
                            signal_strength=receiver.getSignalStrength(),
                            target_info=info,
                        ),
                    )
            finally:
                # Always advance to the next packet in queue: if there has been an exception,
                # it is safer to advance to the next.
                receiver.nextPacket()
        return targets
