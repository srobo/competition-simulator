from __future__ import annotations

from enum import Enum, IntEnum
from typing import Set, List, NamedTuple


class RobotType(Enum):
    FORKLIFT = 'forklift'
    CRANE = 'crane'


class Owner(IntEnum):
    ZONE_0 = 0
    ZONE_1 = 1

    @classmethod
    def zones(cls) -> Set[Owner]:
        return {  # noqa: C416
            owner
            for owner in cls
        }


class Token(NamedTuple):
    owner: Owner
    id: int  # noqa: A003

    def __repr__(self) -> str:
        return f'<{self.owner.name}:{self.id}>'


TOKENS: List[Token] = [
    Token(Owner.ZONE_0, 1),
    Token(Owner.ZONE_1, 4),
]
