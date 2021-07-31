from enum import Enum, IntEnum
from typing import List, NamedTuple


class RobotType(Enum):
    FORKLIFT = 'forklift'
    CRANE = 'crane'


class Owner(IntEnum):
    ZONE_0 = 0
    ZONE_1 = 1
    NULL = -1


class TargetType(IntEnum):
    BEACON = 0
    CONTAINER = 1


class TargetInfo(NamedTuple):
    type: TargetType  # noqa: A003
    owner: Owner
    id: int  # noqa: A003

    def __repr__(self) -> str:
        return f'<{self.type.name}, Owner={self.owner.name}, id={self.id}>'


TOKENS: List[TargetInfo] = [
    TargetInfo(TargetType.BEACON, Owner.NULL, 100),
    TargetInfo(TargetType.BEACON, Owner.NULL, 101),
    TargetInfo(TargetType.BEACON, Owner.NULL, 102),
    TargetInfo(TargetType.BEACON, Owner.NULL, 103),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 1),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 4),
]
