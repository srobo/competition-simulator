from enum import Enum, IntEnum
from typing import List, NamedTuple


class RobotType(Enum):
    FORKLIFT = 'forklift'
    CRANE = 'crane'


class Owner(IntEnum):
    ZONE_0 = 0
    ZONE_1 = 1


class Token(NamedTuple):
    owner: Owner
    id: int  # noqa: A003

    def __repr__(self) -> str:
        return f'<{self.owner.name}:{self.id}>'


TOKENS: List[Token] = [
    Token(Owner.ZONE_0, 1),
    Token(Owner.ZONE_0, 2),
    Token(Owner.ZONE_0, 3),
    Token(Owner.ZONE_0, 4),
    Token(Owner.ZONE_0, 5),
    Token(Owner.ZONE_0, 6),
    Token(Owner.ZONE_0, 7),
    Token(Owner.ZONE_0, 8),
    Token(Owner.ZONE_1, 9),
    Token(Owner.ZONE_1, 10),
    Token(Owner.ZONE_1, 11),
    Token(Owner.ZONE_1, 12),
    Token(Owner.ZONE_1, 13),
    Token(Owner.ZONE_1, 14),
    Token(Owner.ZONE_1, 15),
    Token(Owner.ZONE_1, 16),
]
