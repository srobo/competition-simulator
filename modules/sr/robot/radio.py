import re
import enum
from typing import List, Optional, NamedTuple

from controller import Robot
from sr.robot.coordinates import Point, Vector

TRANSMITTER_MODEL_RE = re.compile(r"^[BTR]\d{0,2}$")


class TransmitterType(enum.Enum):
    BEACON = 'BEACON'
    TOWER = 'TOWER'
    ROBOT = 'ROBOT'


class TransmitterInfo(NamedTuple):
    code: int
    offset: int
    transmitter_type: TransmitterType


TRANSMITTER_MODEL_TYPE_MAP = {
    'B': TransmitterType.BEACON,
    'T': TransmitterType.TOWER,
    'R': TransmitterType.ROBOT,
}

TRANSMITTER_TYPE_OFFSETS = {
    TransmitterType.BEACON: 0,
    TransmitterType.TOWER: 2,
    TransmitterType.ROBOT: 15,
}


def parse_radio_message(message: bytes) -> Optional[TransmitterInfo]:
    """
    Parse the model id of a transmitter model into a `TransmitterInfo`.

    Expected input format is a letter and two digits. The letter indicates the
    type of the transmitter, the digits its "libkoki" 'code'.

    Examples: 'B00', 'B01', 'T02', 'T03', ..., 'R15', 'R16', ...
    """

    # TODO: replace this with the actual comms protocol

    match = TRANSMITTER_MODEL_RE.match(...)
    if match is None:
        return None

    kind, number = message[0], message[1:]

    transmitter_type = TRANSMITTER_MODEL_TYPE_MAP[kind]
    code = int(number)

    type_offset = TRANSMITTER_TYPE_OFFSETS[transmitter_type]

    return TransmitterInfo(
        code=code,
        offset=code - type_offset,
        transmitter_type=transmitter_type,
    )


class Transmitter:
    """
    A snapshot of information about a radio transmitter.
    """

    # Note: properties in the same order as in the docs.

    def __init__(
        self,
        vector: Vector,
        transmitter_info: TransmitterInfo,
        timestamp: float,
    ) -> None:
        self._vector = vector

        self.info = transmitter_info
        self.timestamp = timestamp

    def __repr__(self) -> str:
        return '<{}: {}>'.format(type(self).__name__, ', '.join((
            'info={}'.format(self.info),
            'position={}'.format(self.position),
            'dist={}'.format(self.dist),
        )))

    @property
    def position(self) -> Point:
        """A `Point` describing the position of the transmitter."""
        return Point.from_vector(self._vector)

    @property
    def dist(self) -> float:
        """An alias for `position.polar.length`."""
        return self._vector.magnitude()

    @property
    def rot_y(self) -> float:
        """An alias for `position.polar.rot_y`."""
        return self.position.polar.rot_y


class Beacon(Transmitter):
    """
    A snapshot of information about a radio beacon.
    """


class Tower(Transmitter):
    """
    A snapshot of information about a radio tower.

    Radio towers can be claimed to score points.
    """

    def __init__(
        self,
        vector: Vector,
        transmitter_info: TransmitterInfo,
        timestamp: float,
        claimed_by: Optional[int],
    ) -> None:
        super().__init__(vector, transmitter_info, timestamp)
        self.claimed_by = claimed_by


class Radio:
    """
    Wraps a radio transmitter and reciever unit on the Robot.
    """

    def __init__(self, webot: Robot) -> None:
        self._webot = webot

    def sweep(self) -> List[Transmitter]:
        """
        Sweep for nearby radio transmitters.
        """

    def claim_tower(self) -> None:
        """
        Attempt to claim a nearby tower.

        Your radio has a limited transmission power, so will only be able to
        reach at most a single tower at a time.
        """
