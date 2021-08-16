from __future__ import annotations

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
        return f'<{self.type.name}, owner={self.owner.name}, id={self.id}>'


TOKENS: List[TargetInfo] = [
    TargetInfo(TargetType.BEACON, Owner.NULL, 100),
    TargetInfo(TargetType.BEACON, Owner.NULL, 101),
    TargetInfo(TargetType.BEACON, Owner.NULL, 102),
    TargetInfo(TargetType.BEACON, Owner.NULL, 103),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 1),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 2),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 3),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 4),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 5),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 6),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 7),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 8),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 9),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 10),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 11),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 12),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 13),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 14),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 15),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 16),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_0, 17),
    TargetInfo(TargetType.CONTAINER, Owner.ZONE_1, 18),
]
