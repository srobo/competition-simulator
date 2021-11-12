import re
import sys
import enum
import random
import unittest
from typing import Dict, List, Union, Mapping
from pathlib import Path
from unittest.mock import Mock, patch

from territory_controller import (
    Claimant,
    ClaimLog,
    ActionTimer,
    StationCode,
    TerritoryRoot,
    TERRITORY_LINKS,
    AttachedTerritories,
)

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

from sr.robot3.radio import StationCode as RadioStationCode  # isort:skip


class MockStationCode(str, enum.Enum):
    T0 = 'T0'
    T1 = 'T1'
    T2 = 'T2'
    T3 = 'T3'
    T4 = 'T4'
    T5 = 'T5'
    T6 = 'T6'
    T7 = 'T7'
    T8 = 'T8'


@patch('territory_controller.StationCode', MockStationCode)
class TestAttachedTerritories(unittest.TestCase):
    """
    Test build_attached_capture_trees/get_attached_territories
    Uses a fixed, reduced map:
        z0 ── T0 ── T1 ── T2 ── T3 ── z1
         │         ╱  ╲                │
         └─ T4 ── T5 ─ T6 ── T7 ── T8 ─┘
    """

    _zone_0_territories = {MockStationCode.T0, MockStationCode.T1, MockStationCode.T6}
    _zone_1_territories = {
        MockStationCode.T3,
        MockStationCode.T2,
        MockStationCode.T5,
        MockStationCode.T4,
    }
    _zone_1_disconnected = {MockStationCode.T4, MockStationCode.T5}
    _zone_0_capturable = {
        MockStationCode.T2,
        MockStationCode.T4,
        MockStationCode.T5,
        MockStationCode.T7,
    }
    _zone_1_capturable = {MockStationCode.T1, MockStationCode.T8}
    _zone_0_uncapturable = {MockStationCode.T8, MockStationCode.T3}
    _zone_1_uncapturable = {
        MockStationCode.T0,
        MockStationCode.T4,
        MockStationCode.T5,
        MockStationCode.T6,
        MockStationCode.T7,
    }

    def load_territory_owners(self, claim_log: ClaimLog) -> None:
        for territory in self._zone_0_territories:
            claim_log._station_statuses[territory] = Claimant.ZONE_0  # type: ignore[index]

        for territory in self._zone_1_territories:
            claim_log._station_statuses[territory] = Claimant.ZONE_1  # type: ignore[index]

    @patch('territory_controller.TERRITORY_LINKS', new={
        (TerritoryRoot.z0, MockStationCode.T0),
        (TerritoryRoot.z0, MockStationCode.T4),
        (TerritoryRoot.z1, MockStationCode.T3),
        (TerritoryRoot.z1, MockStationCode.T8),

        (MockStationCode.T0, MockStationCode.T1),
        (MockStationCode.T1, MockStationCode.T2),
        (MockStationCode.T2, MockStationCode.T3),
        (MockStationCode.T4, MockStationCode.T5),
        (MockStationCode.T5, MockStationCode.T6),
        (MockStationCode.T6, MockStationCode.T7),
        (MockStationCode.T7, MockStationCode.T8),
        (MockStationCode.T5, MockStationCode.T1),
        (MockStationCode.T6, MockStationCode.T1),
    })
    @patch('territory_controller.StationCode', MockStationCode)
    def setUp(self) -> None:
        super().setUp()
        claim_log = ClaimLog(record_arena_actions=False)
        self.load_territory_owners(claim_log)
        self.attached_territories = AttachedTerritories(claim_log)
        self.connected_territories = self.attached_territories.build_attached_capture_trees()

    def test_connected_zone_0_territories(self) -> None:
        "test multiple paths and loops don't cause a double entry"

        self.assertEqual(
            self.connected_territories[0],
            self._zone_0_territories,
            'Zone 0 has incorrectly detected connected territories',
        )

    def test_connected_zone_1_territories(self) -> None:
        'test cut-off zones are not included'
        zone_1_attached = {
            station
            for station in self._zone_1_territories
            if station not in self._zone_1_disconnected
        }

        self.assertEqual(
            self.connected_territories[1],
            zone_1_attached,
            'Zone 1 has incorrectly detected connected territories',
        )

    def test_stations_can_capture(self) -> None:
        for station in self._zone_0_capturable:
            capturable = self.attached_territories.can_capture_station(
                station,  # type: ignore[arg-type]
                Claimant.ZONE_0,
                self.connected_territories,
            )
            self.assertTrue(
                capturable,
                f'Zone 0 should be able to capture {station}',
            )

        for station in self._zone_1_capturable:
            capturable = self.attached_territories.can_capture_station(
                station,  # type: ignore[arg-type]
                Claimant.ZONE_1,
                self.connected_territories,
            )
            self.assertTrue(
                capturable,
                f'Zone 1 should be able to capture {station}',
            )

    def test_stations_cant_capture(self) -> None:
        for station in self._zone_0_uncapturable:
            capturable = self.attached_territories.can_capture_station(
                station,  # type: ignore[arg-type]
                Claimant.ZONE_0,
                self.connected_territories,
            )
            self.assertFalse(
                capturable,
                f'Zone 0 should not be able to capture {station}',
            )

        for station in self._zone_1_uncapturable:
            capturable = self.attached_territories.can_capture_station(
                station,  # type: ignore[arg-type]
                Claimant.ZONE_1,
                self.connected_territories,
            )
            self.assertFalse(
                capturable,
                f'Zone 1 should not be able to capture {station}',
            )


class TestAdjacentTerritories(unittest.TestCase):
    'Test the AttachedTerritories initialisation of adjacent_zones'

    def setUp(self) -> None:
        super().setUp()
        claim_log = ClaimLog(record_arena_actions=False)
        self.attached_territories = AttachedTerritories(claim_log)

    @unittest.skip("Territory controller no used with current arena")
    def test_all_links_in_set(self) -> None:
        'test all territory links from Arena.wbt are in TERRITORY_LINKS'
        arena_links = set()
        with (REPO_ROOT / 'worlds' / 'Arena.wbt').open('r') as f:
            for line in f.readlines():
                if 'SRLink' in line:
                    arena_links.add(re.sub(r'.*DEF (.*) SRLink .*\n', r'\1', line))

        territory_links_strs = {'-'.join(link) for link in TERRITORY_LINKS}

        self.assertEqual(
            arena_links,
            territory_links_strs,
            'TERRITORY_LINKS differs from links in Arena.wbt',
        )

    def test_all_territories_linked(self) -> None:
        'test every territory exists in keys'
        station_codes = {station.value for station in StationCode}
        station_codes.update({zone.value for zone in TerritoryRoot})
        adjacent_stations = set(self.attached_territories.adjacent_zones.keys())

        self.assertEqual(
            station_codes,
            adjacent_stations,
            'Not all territories are linked',
        )

    def test_omitted_start_zones(self) -> None:
        'test for incorrect links back to z0/z1'

        for station, links in self.attached_territories.adjacent_zones.items():
            self.assertNotIn(
                TerritoryRoot.z0,
                links,
                f'Zone 0 starting zone incorrectly appears in {station.value} links',
            )

            self.assertNotIn(
                TerritoryRoot.z1,
                links,
                f'Zone 1 starting zone incorrectly appears in {station.value} links',
            )


class TestMatchingStationCode(unittest.TestCase):

    def test_radio_matches_territory_controller(self) -> None:
        station_codes = {station.value for station in StationCode}
        radio_station_codes = {station.value for station in RadioStationCode}
        self.assertEqual(
            station_codes,
            radio_station_codes,
            "StationCode enums differ between territory_controller and sr.robot3.radio",
        )

    @unittest.skip("Territory controller not used with current arena")
    def test_matches_arena_file(self) -> None:
        "test StationCode matches SRTerritory nodes in Arena.wbt"

        arena_territories = set()
        with (REPO_ROOT / 'worlds' / 'Arena.wbt').open('r') as f:
            for line in f.readlines():
                if 'SRTerritory' in line:
                    arena_territories.add(re.sub(r'.*DEF (.*) SRTerritory .*\n', r'\1', line))

        station_codes = {station.value for station in StationCode}

        self.assertEqual(
            station_codes,
            arena_territories,
            "StationCode values differs from territories in Arena.wbt",
        )


class TestLiveScoring(unittest.TestCase):
    "Test the live scoring computed in the claim log using tests from the scorer"
    _tla_to_zone = {
        'ABC': Claimant.ZONE_0,
        'DEF': Claimant.ZONE_1,
    }

    def calculate_scores(
        self,
        territory_claims: List[Dict[str, Union[str, int, float]]],
    ) -> Mapping[Claimant, int]:
        claim_log = ClaimLog(record_arena_actions=False)

        for claim in territory_claims:
            territory = StationCode(claim['station_code'])
            claimant = Claimant(int(claim['zone']))
            claim_log._station_statuses[territory] = claimant

        return claim_log.get_scores()

    def assertScores(
        self,
        expected_scores_tla: Mapping[str, int],
        territory_claims: List[Dict[str, Union[str, int, float]]],
    ) -> None:
        actual_scores = self.calculate_scores(territory_claims)

        # swap the TLAs used by the scorer with claimant zones
        expected_scores: Mapping[Claimant, int] = {
            self._tla_to_zone[tla]: score
            for tla, score in expected_scores_tla.items()
        }

        self.assertEqual(expected_scores, actual_scores, "Wrong scores")

    # All tests below this line are copied from the scorer
    def test_no_claims(self) -> None:
        self.assertScores({
            'ABC': 0,
            'DEF': 0,
        }, [])

    def test_single_claim(self) -> None:
        self.assertScores({
            'ABC': 2,
            'DEF': 0,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4.432,
            },
        ])

    def test_two_claims_same_territory(self) -> None:
        self.assertScores({
            'ABC': 0,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
        ])

    def test_two_concurrent_territories(self) -> None:
        self.assertScores({
            'ABC': 2,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 0,
                'station_code': 'EY',
                'time': 5,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5.01,
            },
        ])

    def test_two_isolated_territories(self) -> None:
        self.assertScores({
            'ABC': 2,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
            {
                'zone': 0,
                'station_code': 'EY',
                'time': 5.01,
            },
        ])

    def test_both_teams_claim_both_territories(self) -> None:
        # But only one of them holds both at the same time
        self.assertScores({
            'ABC': 2,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
            {
                'zone': 1,
                'station_code': 'EY',
                'time': 6,
            },
            {
                'zone': 0,
                'station_code': 'EY',
                'time': 7,
            },
        ])

    def test_territory_becoming_unclaimed_after_it_was_claimed(self) -> None:
        self.assertScores({
            'ABC': 0,
            'DEF': 0,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 6,
            },
            {
                'zone': -1,
                'station_code': 'PN',
                'time': 7,
            },
        ])

    def test_unclaimed_territory_with_others_claimed(self) -> None:
        self.assertScores({
            'ABC': 2,
            'DEF': 2,
        }, [
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 4,
            },
            {
                'zone': 1,
                'station_code': 'PN',
                'time': 5,
            },
            {
                'zone': 0,
                'station_code': 'PN',
                'time': 6,
            },
            {
                'zone': 0,
                'station_code': 'EY',
                'time': 7,
            },
            {
                'zone': -1,
                'station_code': 'PN',
                'time': 8,
            },
            {
                'zone': 1,
                'station_code': 'SZ',
                'time': 9,
            },
        ])

    def test_bronze_claim(self) -> None:
        self.assertScores({
            'ABC': 4,
            'DEF': 0,
        }, [
            {
                'zone': 0,
                'station_code': 'HA',
                'time': 3.14,
            },
        ])

    def test_gold_claim(self) -> None:
        self.assertScores({
            'ABC': 8,
            'DEF': 0,
        }, [
            {
                'zone': 0,
                'station_code': 'YT',
                'time': 3.14,
            },
        ])


class TestActionTimer(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.action_timer = ActionTimer(1.9)

    def assertBegunInsideDuration(self, duration: float, expected_result: bool) -> None:
        start_time = random.uniform(0, 1000)
        self.action_timer.begin_action(StationCode.PN, Claimant.ZONE_1, start_time)

        actual_result = self.action_timer.has_begun_action_in_time_window(
            StationCode.PN,
            Claimant.ZONE_1,
            start_time + duration,
        )

        self.assertEqual(
            actual_result,
            expected_result,
            f"Timer gave incorect result with duration {duration}",
        )

    def test_exact_time(self) -> None:
        self.assertBegunInsideDuration(2, True)

    def test_too_short_time(self) -> None:
        self.assertBegunInsideDuration(1.7, False)

    def test_too_long_time(self) -> None:
        self.assertBegunInsideDuration(2.2, False)

    def test_marginal_short_time(self) -> None:
        self.assertBegunInsideDuration(1.72, True)

    def test_marginal_long_time(self) -> None:
        self.assertBegunInsideDuration(2.08, True)

    def test_different_stations(self) -> None:
        start_time = random.uniform(0, 1000)
        # Start action with station PN
        self.action_timer.begin_action(StationCode.PN, Claimant.ZONE_1, start_time)

        # Attempt to complete action with SZ
        result = self.action_timer.has_begun_action_in_time_window(
            StationCode.SZ,
            Claimant.ZONE_1,
            start_time + 1.9,
        )

        self.assertFalse(result)

    def test_different_claimants(self) -> None:
        start_time = random.uniform(0, 1000)
        # Zone 0 starts action
        self.action_timer.begin_action(StationCode.PN, Claimant.ZONE_0, start_time)

        # Zone 1 attempts to complete action
        result = self.action_timer.has_begun_action_in_time_window(
            StationCode.PN,
            Claimant.ZONE_1,
            start_time + 1.9,
        )

        self.assertFalse(result)


class TestActionTimerTick(unittest.TestCase):
    "Test the progress_callback functionality of the ActionTimer"
    def setUp(self) -> None:
        super().setUp()
        self.progress_callback = Mock()
        self.action_duration = 2
        self.action_timer = ActionTimer(self.action_duration, self.progress_callback)

    def assertTickCall(
        self,
        start_time: float,
        end_time: float,
        prev_progress: float,
    ) -> float:
        self.action_timer.tick(end_time)
        # recalculate the duration to avoid floating-point precision errors
        progress = (end_time - start_time) / self.action_duration

        self.progress_callback.assert_called_with(
            StationCode.BE,
            Claimant.ZONE_1,
            progress,
            prev_progress,
        )
        return progress

    def assertCallCount(self, call_count: int, context: str) -> None:
        self.assertEqual(
            self.progress_callback.call_count,
            call_count,
            f"Incorrect number of calls of progress_callback {context}"
            f" ({self.progress_callback.call_args_list})",
        )

    def test_successful_completion(self) -> None:
        """
        Test that progress_callback is called with appropriate arguments at the start
        and completion of the timer. Namely the progress parameter should be 0 when the
        timer starts and TIMER_COMPLETE when the timer action is successfully completed.
        Once TIMER_COMPLETE or TIMER_EXPIRE is parsed to progress_callback, the timer item
        is removed from the internal dict and should not cause progress_callback to be
        called on subsequent calls of tick().
        """
        start_time = random.uniform(0, 1000)
        self.action_timer.begin_action(StationCode.BE, Claimant.ZONE_1, start_time)
        self.progress_callback.assert_called_with(StationCode.BE, Claimant.ZONE_1, 0, 0)

        used_duration = random.uniform(1.8, 2.2)
        self.action_timer.has_begun_action_in_time_window(
            StationCode.BE,
            Claimant.ZONE_1,
            start_time + used_duration,
        )
        self.progress_callback.assert_called_with(
            StationCode.BE,
            Claimant.ZONE_1,
            ActionTimer.TIMER_COMPLETE,
            0,
        )

        self.action_timer.tick(start_time + used_duration)
        self.assertCallCount(2, "after action completion")

    def test_expired_timer(self) -> None:
        """
        Test that progress_callback is called with appropriate arguments at the start
        and expiry of the timer. Namely the progress parameter should be 0
        when the timer starts and TIMER_EXPIRE when the timer expires.
        """
        start_time = random.uniform(0, 1000)
        self.action_timer.begin_action(StationCode.BE, Claimant.ZONE_1, start_time)
        self.progress_callback.assert_called_with(StationCode.BE, Claimant.ZONE_1, 0, 0)

        # make timer expire
        used_duration = random.uniform(2.3, 10)
        self.action_timer.tick(start_time + used_duration)
        self.progress_callback.assert_called_with(
            StationCode.BE,
            Claimant.ZONE_1,
            ActionTimer.TIMER_EXPIRE,
            0,
        )

        self.action_timer.tick(start_time + used_duration)
        self.assertCallCount(2, "after timer expired")

    def test_tick_call(self) -> None:
        """
        Test that the progress_callback method is called will the given progress
        on each call to ActionTimer.tick
        """
        start_time = random.uniform(0, 1000)
        self.action_timer.begin_action(StationCode.BE, Claimant.ZONE_1, start_time)

        prev_progress = self.assertTickCall(start_time, start_time + 0.9, 0)

        self.assertTickCall(start_time, start_time + 2.1, prev_progress)

        self.assertCallCount(3, "")
