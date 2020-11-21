import struct
from math import atan2
from typing import List, NewType, Optional, NamedTuple
from threading import Lock

from controller import Robot
from sr.robot.coordinates import Vector

BROADCASTS_PER_SECOND = 10

StationCode = NewType('StationCode', str)
Claimant = NewType('Claimant', int)

UNCLAIMED = Claimant(-1)


class TransmitterInfo(NamedTuple):
    station_code: StationCode
    owned_by: Optional[Claimant]


def parse_radio_message(message: bytes, zone: int) -> Optional[TransmitterInfo]:
    try:
        station_code, owned_by = struct.unpack("!2sb", message)
        owned_by = owned_by if owned_by is not UNCLAIMED else None
        return TransmitterInfo(station_code=station_code, owned_by=owned_by)
    except ValueError:
        print("Robot starting in zone {zone} received malformed message.")
        return None


class Transmitter:
    """
    A snapshot of information about a radio transmitter.
    """

    # Note: properties in the same order as in the docs.

    def __init__(
        self,
        vector: Vector,
        signal_strength: float,
        transmitter_info: TransmitterInfo,
    ) -> None:
        self.strength = signal_strength
        x, y, z = vector.data
        self.bearing = atan2(z, x)  # TODO confirm this is correct
        self.info = transmitter_info

    def __repr__(self) -> str:
        return '<{}: {}>'.format(type(self).__name__, ', '.join((
            'info={}'.format(self.info),
            'bearing={}'.format(self.bearing),
            'strength={}'.format(self.strength),
        )))


class Radio:
    """
    Wraps a radio transmitter and reciever unit on the Robot.
    """

    def __init__(self, webot: Robot, zone: int, step_lock: Lock) -> None:
        self._webot = webot
        self._receiver = webot.getReceiver("robot receiver")
        self._receiver.enable(1)
        self._emitter = webot.getEmitter("robot emitter")
        self._zone = zone
        self._step_lock = step_lock

    def sweep(self) -> List[Transmitter]:
        """
        Sweep for nearby radio transmitters.
        Sweeping takes 0.1 seconds
        """
        receiver = self._receiver
        # Clear the buffer
        while receiver.getQueueLength():
            receiver.nextPacket()
        # Wait 1 sweep
        with self._step_lock:
            self._webot.step(int(1000 / BROADCASTS_PER_SECOND))
        # Read the buffer
        transmitters = []
        while receiver.getQueueLength():
            try:
                info = parse_radio_message(receiver.getData(), self._zone)
                if info:
                    transmitters.append(
                        Transmitter(
                            vector=Vector(receiver.getEmitterDirection()),
                            signal_strength=receiver.getSignalStrength(),
                            transmitter_info=info,
                        ),
                    )
            finally:
                # Always advance to the next packet in queue: if there has been an exception,
                # it is safer to advance to the next.
                receiver.nextPacket()
        return transmitters

    def claim_territory(self) -> None:
        """
        Attempt to claim any nearby territories.

        Your radio has a limited transmission power, so will only be able to claim a territory
        if you're inside its receiving range.
        """
        self._emitter.send(struct.pack("!B", self._zone))
