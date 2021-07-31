from enum import Enum, IntEnum
from typing import List, NamedTuple


class RobotType(Enum):
    FORKLIFT = 'forklift'
    CRANE = 'crane'


class Owner(IntEnum):
    ZONE_0 = 0
    ZONE_1 = 1
    BEACON = -1


class Token(NamedTuple):
    owner: Owner
    id: int  # noqa: A003

    def __repr__(self) -> str:
        return f'<{self.owner.name}:{self.id}>'


TOKENS: List[Token] = [
    Token(Owner.BEACON, 100),
    Token(Owner.BEACON, 101),
    Token(Owner.BEACON, 102),
    Token(Owner.BEACON, 103),
    Token(Owner.ZONE_0, 1),
    Token(Owner.ZONE_1, 4),
]
