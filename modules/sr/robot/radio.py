import struct
from math import pi, atan2
from typing import List, NewType, Optional, NamedTuple
from threading import Lock

from controller import Robot
from sr.robot.coordinates import Vector

BROADCASTS_PER_SECOND = 10

StationCode = NewType('StationCode', str)
Claimant = NewType('Claimant', int)

UNCLAIMED = Claimant(-1)


class TargetInfo(NamedTuple):
    station_code: StationCode
    owned_by: Optional[Claimant]


def parse_radio_message(message: bytes, zone: int) -> Optional[TargetInfo]:
    try:
        station_code, owned_by = struct.unpack("!2sb", message)
        station_code = station_code.decode('utf-8')
        owned_by = owned_by if owned_by is not UNCLAIMED else None
        return TargetInfo(station_code=station_code, owned_by=owned_by)
    except ValueError:
        print("Robot starting in zone {zone} received malformed message.")  # noqa:T001
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
    ) -> 'Target':
        x, _, z = vector.data  # 2-dimensional bearing in the xz plane, elevation is ignored
        bearing = pi - atan2(x, z)
        bearing = bearing - (2 * pi) if bearing > pi else bearing  # Normalize to (-pi, pi)
        return cls(bearing=bearing, signal_strength=signal_strength, target_info=target_info)

    def __repr__(self) -> str:
        return '<{}: {}>'.format(type(self).__name__, ', '.join((
            'info={}'.format(self.target_info),
            'bearing={}'.format(self.bearing),
            'strength={}'.format(self.signal_strength),
        )))


class Radio:
    """
    Wraps a radio target and reciever unit on the Robot.
    """

    def __init__(self, webot: Robot, zone: int, step_lock: Lock) -> None:
        self._webot = webot
        self._receiver = webot.getReceiver("robot receiver")
        self._receiver.enable(1)
        self._emitter = webot.getEmitter("robot emitter")
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

    def claim_territory(self) -> None:
        """
        Attempt to claim any nearby territories.

        The radio has a limited transmission power, so will only be able to claim a territory
        if you're inside its receiving range.
        """
        self._emitter.send(struct.pack("!B", self._zone))
