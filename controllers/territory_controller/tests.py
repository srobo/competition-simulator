import re
import random
import unittest
from typing import Dict, List, Union, Mapping
from pathlib import Path
from unittest.mock import Mock

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


class TestAttachedTerritories(unittest.TestCase):
    'Test build_attached_capture_trees/get_attached_territories'

    _zone_0_territories = {
        StationCode.BG,
        StationCode.TS,
        StationCode.OX,
        StationCode.VB,
        StationCode.PL,
    }
    _zone_1_territories = {StationCode.PN, StationCode.EY, StationCode.PO, StationCode.YL}
    _zone_1_disconnected = {StationCode.PN, StationCode.EY}

    def load_territory_owners(self, claim_log: ClaimLog) -> None:
        # territories BG, TS, OX, VB, etc. owned by zone 0
        for territory in self._zone_0_territories:
            claim_log._station_statuses[territory].owner = Claimant.ZONE_0

        # territories PN, EY, PO, YL owned by zone 1
        for territory in self._zone_1_territories:
            claim_log._station_statuses[territory].owner = Claimant.ZONE_1

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
        for station in {StationCode.PN, StationCode.EY, StationCode.TS, StationCode.SZ}:
            capturable = self.attached_territories.can_capture_station(
                station,
                Claimant.ZONE_0,
                self.connected_territories,
            )
            self.assertEqual(
                capturable,
                True,
                f'Zone 0 should be able to capture {station}',
            )

        for station in {StationCode.BN, StationCode.SZ, StationCode.HV}:
            capturable = self.attached_territories.can_capture_station(
                station,
                Claimant.ZONE_1,
                self.connected_territories,
            )
            self.assertEqual(
                capturable,
                True,
                f'Zone 1 should be able to capture {station}',
            )

    def test_stations_cant_capture(self) -> None:
        for station in {StationCode.YL, StationCode.PO, StationCode.HA}:
            capturable = self.attached_territories.can_capture_station(
                station,
                Claimant.ZONE_0,
                self.connected_territories,
            )
            self.assertEqual(
                capturable,
                False,
                f'Zone 0 should not be able to capture {station}',
            )

        for station in {
            StationCode.PN,
            StationCode.EY,
            StationCode.VB,
            StationCode.SW,
        }:
            capturable = self.attached_territories.can_capture_station(
                station,
                Claimant.ZONE_1,
                self.connected_territories,
            )
            self.assertEqual(
                capturable,
                False,
                f'Zone 1 should not be able to capture {station}',
            )


class TestAdjacentTerritories(unittest.TestCase):
    'Test the AttachedTerritories initialisation of adjacent_zones'

    def setUp(self) -> None:
        super().setUp()
        claim_log = ClaimLog(record_arena_actions=False)
        self.attached_territories = AttachedTerritories(claim_log)

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
        'test PN, YL for incorrect links back to z0/z1'

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

    def test_VB_links(self) -> None:
        'test BE for correct links'
        self.assertEqual(
            self.attached_territories.adjacent_zones[StationCode.VB],
            {
                StationCode.BG,
                StationCode.EY,
                StationCode.OX,
                StationCode.BE,
                StationCode.PL,
            },
            'Territory VB has incorrect territory links',
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
            claimant = Claimant(claim['zone'])
            claim_log._station_statuses[territory].owner = claimant

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

    def assertTickCall(self, start_time: float, end_time: float) -> None:
        self.action_timer.tick(end_time)
        self.progress_callback.assert_called_with(
            StationCode.BE,
            Claimant.ZONE_1,
            # recalculate the duration to avoid floating-point precision errors
            (end_time - start_time) / self.action_duration,
        )

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
        self.progress_callback.assert_called_with(StationCode.BE, Claimant.ZONE_1, 0)

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
        self.progress_callback.assert_called_with(StationCode.BE, Claimant.ZONE_1, 0)

        # make timer expire
        used_duration = random.uniform(2.3, 10)
        self.action_timer.tick(start_time + used_duration)
        self.progress_callback.assert_called_with(
            StationCode.BE,
            Claimant.ZONE_1,
            ActionTimer.TIMER_EXPIRE,
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

        self.assertTickCall(start_time, start_time + 0.9)

        self.assertTickCall(start_time, start_time + 2.1)

        self.assertCallCount(3, "")
