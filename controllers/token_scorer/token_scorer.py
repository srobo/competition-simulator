import sys
import enum
from typing import Dict, List, Tuple, NamedTuple
from pathlib import Path

# Webots specific library
from controller import Field, Supervisor

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

from webots_utils import node_from_def  # isort:skip
import controller_utils  # isort:skip

SCORE_UPDATES_PER_SECOND = 10

FLOOR_TOKEN_VALUE = 1
PLATFORM_EXTRA_TOKEN_VALUE = 1


class Point(NamedTuple):
    # We are only tracking tokens on a 2D plane
    x: float
    y: float


class Owner(enum.IntEnum):
    ZONE_0 = 0
    ZONE_1 = 1


class Token(NamedTuple):
    owner: Owner
    id: int  # noqa: A003

    def __repr__(self) -> str:
        return f'<{self.owner.name}:{self.id}>'


SHIP_SCORING_ZONE = (Point(-0.75, 0.5), Point(0.75, -3))
ZONE_0_STACK_SCORING_ZONE = (Point(-0.75, 0.5), Point(0.75, -0.5))
ZONE_1_STACK_SCORING_ZONE = (Point(-0.75, -2), Point(0.75, -3))

TOKENS: List[Token] = [
    Token(Owner.ZONE_0, 1),
    Token(Owner.ZONE_1, 4),
]


class ClaimLogEntry(NamedTuple):
    token_code: Token
    token_value: int
    claim_time: float


class ClaimLog:
    def __init__(self, record_arena_actions: bool) -> None:
        self._record_arena_actions = record_arena_actions

        self._log: List[ClaimLogEntry] = []
        # Starting with a dirty log ensures the structure is written for every match.
        self._log_is_dirty = True

    def _record_log_entry(self, entry: ClaimLogEntry) -> None:
        self._log.append(entry)
        self._log_is_dirty = True

    def log_token_value_change(
        self,
        token_code: Token,
        token_value: int,
        claim_time: float,
    ) -> None:
        self._record_log_entry(ClaimLogEntry(token_code, token_value, claim_time))
        print(  # noqa:T001
            f"{token_code} NOW WORTH {token_value} TO {token_code.owner.name} "
            f"AT {claim_time}s",
        )

    def record_captures(self) -> None:
        if not self._record_arena_actions:
            self._log_is_dirty = False  # Stop links and displays being updated every timestep
            return

        if not self._log_is_dirty:
            # Don't write the log if nothing new has happened.
            return

        controller_utils.record_arena_data({'token_claims': [
            {
                'zone': claim.token_code.owner.value,
                'token_index': claim.token_code.id,
                'token_value': claim.token_value,
                'time': claim.claim_time,
            }
            for claim in self._log
        ]})

        self._log_is_dirty = False

    def is_dirty(self) -> bool:
        return self._log_is_dirty


def order_zone_points(zone: Tuple[Point, Point]) -> Tuple[Point, Point]:
    'Sort points so the first point has the lower x and y coordinates'
    return (
        Point(min(zone[0].x, zone[1].x), min(zone[0].y, zone[1].y)),
        Point(max(zone[0].x, zone[1].x), max(zone[0].y, zone[1].y)),
    )


class TokenScorer:
    def __init__(
        self,
        claim_log: ClaimLog,
        ship_zone: Tuple[Point, Point],
        zone_0_stack: Tuple[Point, Point],
        zone_1_stack: Tuple[Point, Point],
    ) -> None:
        self._claim_log = claim_log
        self._robot = Supervisor()
        self.ship_zone = order_zone_points(ship_zone)
        self.stack_zones = [order_zone_points(zone_0_stack), order_zone_points(zone_1_stack)]

        self._token_statuses: Dict[Token, int] = {
            code: 0 for code in TOKENS
        }

        self._token_location_fields: Dict[Token, Field] = {
            code: node_from_def(
                self._robot,
                f'{code.owner.name}_{code.id}',
            ).getField('translation') for code in TOKENS
        }

    def token_in_zone(self, token_location: Point, zone: Tuple[Point, Point]) -> bool:
        # zone[0] < zone[1]
        if token_location.x < zone[0].x or zone[1].x < token_location.x:
            # token is outside the zone in the x-direction
            return False
        if token_location.y < zone[0].y or zone[1].y < token_location.y:
            # token is outside the zone in the x-direction
            return False

        return True

    def get_token_value(
        self,
        owner: Owner,
        location: Point,
    ) -> int:
        value = 0

        if self.token_in_zone(location, self.ship_zone):
            value = FLOOR_TOKEN_VALUE

        if self.token_in_zone(location, self.stack_zones[owner]):
            value += PLATFORM_EXTRA_TOKEN_VALUE

        return value

    def get_token_location(
        self,
        token_code: Token,
    ) -> Point:
        position = self._token_location_fields[token_code].getSFVec3f()
        # remap the Webots coordinate system to a 2D plane with Y pointing north
        return Point(position[2], position[0])

    def process_token_locations(self) -> None:
        for token_code in TOKENS:
            position = self.get_token_location(token_code)
            token_value = self.get_token_value(token_code.owner, position)

            if token_value != self._token_statuses[token_code]:
                # token has moved between scoring zones
                self._claim_log.log_token_value_change(
                    token_code,
                    token_value,
                    self._robot.getTime(),
                )
            self._token_statuses[token_code] = token_value

    def main(self) -> None:
        token_scan_step = 1000 / SCORE_UPDATES_PER_SECOND
        while True:
            self.process_token_locations()
            self._robot.step(int(token_scan_step))


if __name__ == "__main__":
    claim_log = ClaimLog(record_arena_actions=(
        controller_utils.get_match_file().exists() and
        controller_utils.get_robot_mode() == 'comp'
    ))
    token_scorer = TokenScorer(
        claim_log,
        SHIP_SCORING_ZONE,
        ZONE_0_STACK_SCORING_ZONE,
        ZONE_1_STACK_SCORING_ZONE,
    )
    token_scorer.main()
