import sys
import struct
from math import cos, sin, sqrt, atan2
from typing import cast, Dict, List, Tuple, NamedTuple
from pathlib import Path

# Webots specific library
from controller import LED, Robot, Receiver, Supervisor

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

from sr.robot.utils import get_robot_device  # isort:skip
from shared_utils import Owner, TOKENS, TargetInfo, TargetType  # isort:skip
import controller_utils  # isort:skip

SCORE_UPDATES_PER_SECOND = 10

FLOOR_TOKEN_VALUE = 1
PLATFORM_EXTRA_TOKEN_VALUE = 2


class Point(NamedTuple):
    # We are only tracking tokens on a 2D plane, with Y as north
    x: float
    y: float


SHIP_SCORING_ZONE = (Point(-0.75, 0.5), Point(0.75, -3))
ZONE_0_STACK_SCORING_ZONE = (Point(-0.75, 0.5), Point(0.75, -0.5))
ZONE_1_STACK_SCORING_ZONE = (Point(-0.75, -2), Point(0.75, -3))


class ClaimLogEntry(NamedTuple):
    token_code: TargetInfo
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
        token_code: TargetInfo,
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


class SevenSeg:
    """
    A driver to display a decimal digit on 7 LEDs

    ┌─0─┐
    5   1
    ├─6─┤
    4   2
    └─3─┘
    """
    lut = [
        (True, True, True, True, True, True, False),  # 0
        (False, True, True, False, False, False, False),  # 1
        (True, True, False, True, True, False, True),  # 2
        (True, True, True, True, False, False, True),  # 3
        (False, True, True, False, False, True, True),  # 4
        (True, False, True, True, False, True, True),  # 5
        (True, False, True, True, True, True, True),  # 6
        (True, True, True, False, False, False, False),  # 7
        (True, True, True, True, True, True, True),  # 8
        (True, True, True, True, False, True, True),  # 9
    ]

    def __init__(self, webot: Robot, led_basename: str):
        self._leds = [
            get_robot_device(webot, f'{led_basename} {led}', LED)
            for led in range(7)
        ]

    def set_value(self, value: int) -> None:
        if value < 0 or value > 9:
            raise ValueError(f"{value} cannot be represented on a seven segment digit")
        for i in range(7):
            self._leds[i].set(self.lut[value][i])


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

        self.score_displays = {
            Owner.ZONE_0: (
                SevenSeg(self._robot, 'Score 0 low'),
                SevenSeg(self._robot, 'Score 0 high'),
            ),
            Owner.ZONE_1: (
                SevenSeg(self._robot, 'Score 1 low'),
                SevenSeg(self._robot, 'Score 1 high'),
            ),
        }

        self._token_statuses: Dict[TargetInfo, int] = {
            code: 0 for code in TOKENS
        }

        self._scoring_receivers: Dict[Receiver, Point] = {
            get_robot_device(self._robot, 'token scorer', Receiver): Point(0, -1.25),
        }

        timestep = int(self._robot.getBasicTimeStep())
        for receiver in self._scoring_receivers.keys():
            receiver.enable(timestep)

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
        token_vector: Tuple[float, float, float],
        signal_strength: float,
        receiver_location: Point,
    ) -> Point:
        token_distance = 1 / sqrt(signal_strength)
        # bearing from north
        token_bearing = atan2(token_vector[2], token_vector[0])

        # calculate the ratio between direct distance and distance in a 2D plane
        height_offset_multiplier = cos(atan2(
            token_vector[1],
            sqrt(token_vector[2] ** 2 + token_vector[0] ** 2),
        ))

        position = (
            token_distance * sin(token_bearing) * height_offset_multiplier,
            token_distance * cos(token_bearing) * height_offset_multiplier,
        )
        # map to a 2D plane with Y pointing north
        return Point(position[0] + receiver_location[0], position[1] + receiver_location[1])

    def process_detected_token(
        self,
        data: bytes,
        token_vector: Tuple[float, float, float],
        signal_strength: float,
        receiver_location: Point,
    ) -> TargetInfo:
        token_type, token_code, owner = struct.unpack("!bBb", data)
        token = TargetInfo(TargetType(token_type), Owner(owner), token_code)

        position = self.get_token_location(
            token_vector,
            signal_strength,
            receiver_location,
        )

        token_value = self.get_token_value(owner, position)

        if token_value != self._token_statuses[token]:
            # token has moved between scoring zones
            self._claim_log.log_token_value_change(
                token,
                token_value,
                self._robot.getTime(),
            )
            self._token_statuses[token] = token_value

        return token

    def process_token_locations(self) -> None:
        observed_tokens: List[TargetInfo] = []

        for receiver, receiver_location in self._scoring_receivers.items():
            while receiver.getQueueLength():
                try:
                    data = receiver.getData()
                    vector = receiver.getEmitterDirection()
                    signal_strength = receiver.getSignalStrength()
                    observed_tokens.append(
                        self.process_detected_token(
                            data,
                            cast(Tuple[float, float, float], vector),
                            signal_strength,
                            receiver_location,
                        ),
                    )
                finally:
                    # Always advance to the next packet in queue:
                    # if there has been an exception, it is safer to advance to the next.
                    receiver.nextPacket()

        # remove score from tokens that are outside the scorable zone
        for token in TOKENS:
            if token in observed_tokens:
                continue

            if self._token_statuses[token] == 0:
                continue

            self._claim_log.log_token_value_change(
                token,
                0,
                self._robot.getTime(),
            )
            self._token_statuses[token] = 0

    def get_scores(self) -> Dict[Owner, int]:
        """
        Get the current scores.

        The returned dict will always include all the claimants as keys.
        """
        zone_scores: Dict[Owner, int] = {}

        for zone in Owner:
            zone_scores[zone] = sum(
                value
                for token, value in self._token_statuses.items()
                if token.owner == zone
            )

        return zone_scores

    def update_displayed_scores(self) -> None:
        scores = self.get_scores()

        for zone, score in scores.items():
            try:
                display = self.score_displays[zone]
            except KeyError:
                continue

            score_digits = (score % 10, int(score / 10))

            display[0].set_value(score_digits[0])
            display[1].set_value(score_digits[1])

    def main(self) -> None:
        token_scan_step = 1000 / SCORE_UPDATES_PER_SECOND
        while True:
            self.process_token_locations()
            if self._claim_log.is_dirty():
                self.update_displayed_scores()

            self._claim_log.record_captures()
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
