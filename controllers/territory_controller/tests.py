import re
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from territory_controller import (
    Claimant,
    ClaimLog,
    StationCode,
    TerritoryRoot,
    TERRITORY_LINKS,
    AttachedTerritories,
    TerritoryController,
    LOCKED_OUT_AFTER_CLAIM,
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
        StationCode.BE,
        StationCode.SZ,
    }
    _zone_1_territories = {StationCode.PN, StationCode.EY, StationCode.PO, StationCode.YL}
    _zone_1_disconnected = {StationCode.PN, StationCode.EY}

    def load_territory_owners(self, claim_log: ClaimLog) -> None:
        # territories BG, TS, OX, VB, BE, SZ owned by zone 0
        for territory in self._zone_0_territories:
            claim_log._station_statuses[territory] = Claimant.ZONE_0

        # territories PN, EY, PO, YL owned by zone 1
        for territory in self._zone_1_territories:
            claim_log._station_statuses[territory] = Claimant.ZONE_1

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
        for station in {StationCode.PN, StationCode.EY, StationCode.SW, StationCode.PO}:
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

        for station in {StationCode.BE, StationCode.SW, StationCode.HV}:
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
        for station in {StationCode.YL, StationCode.BN, StationCode.HV}:
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
            StationCode.SZ,
            StationCode.BN,
            StationCode.VB,
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

    def test_BE_links(self) -> None:
        'test BE for correct links'
        self.assertEqual(
            self.attached_territories.adjacent_zones[StationCode.BE],
            {StationCode.EY, StationCode.VB, StationCode.SZ, StationCode.PO},
            'Territory BE has incorrect territory links',
        )


class TestTerritoryLockout(unittest.TestCase):
    "Test that individual territories become 'locked' when claimed a set number of times"

    _zone_0_territories = {StationCode.PN, StationCode.EY}
    _zone_1_territories = {StationCode.YL, StationCode.PO}

    def load_territory_owners(self, claim_log: ClaimLog) -> None:
        for territory in self._zone_0_territories:
            claim_log._station_statuses[territory] = Claimant.ZONE_0

        for territory in self._zone_1_territories:
            claim_log._station_statuses[territory] = Claimant.ZONE_1

    @patch('controller.Supervisor.getFromDef')
    @patch('territory_controller.get_robot_device')
    @patch('territory_controller.TerritoryController.set_score_display')
    def setUp(
        self,
        mock_score_display: Mock,
        mock_get_robot: Mock,
        mock_getFromDef: Mock,
    ) -> None:
        super().setUp()
        claim_log = ClaimLog(record_arena_actions=False)
        self.load_territory_owners(claim_log)
        self.attached_territories = AttachedTerritories(claim_log)
        self.territory_controller = TerritoryController(
            claim_log,
            self.attached_territories,
        )

    @patch('controller.Supervisor.getFromDef')
    def test_territory_lockout(self, mock_getFromDef: Mock) -> None:
        """
        Test a territory is locked after the correct number of claims and
        disconnected territories aren't also locked
        """
        for i in range(LOCKED_OUT_AFTER_CLAIM):
            # lock status is tested before capturing since the final
            # iteration will lock the territory
            for station in [StationCode.BE, StationCode.SZ]:  # assert BE, SZ unlocked
                self.assertFalse(
                    self.territory_controller._claim_log.is_locked(station),
                    f"Territory {station.value} locked early on claim {i}",
                )

            # capture BE, SZ by alternating sides
            if i % 2 == 0:
                claimant = Claimant.ZONE_0
            else:
                claimant = Claimant.ZONE_1
            for station in [StationCode.BE, StationCode.SZ]:
                # when BE becomes locked SZ will be uncapturable
                # which will prevent it from also locking
                self.territory_controller.claim_territory(station, claimant, 0)

        # assert BE locked
        self.assertTrue(
            self.territory_controller._claim_log.is_locked(StationCode.BE),
            f"Territory BE failed to lock after {LOCKED_OUT_AFTER_CLAIM} claims",
        )
        # assert SZ unlocked
        self.assertFalse(
            self.territory_controller._claim_log.is_locked(StationCode.SZ),
            f"Territory {station.value} incorrectly locked alongside station BE",
        )

    @patch('controller.Supervisor.getFromDef')
    def test_self_lockout(self, mock_getFromDef: Mock) -> None:
        "Test a territory is locked after the correct number of claims by its own owner"
        for i in range(LOCKED_OUT_AFTER_CLAIM):
            # lock status is tested before capturing since the final
            # iteration will lock the territory
            self.assertFalse(  # assert BE, SZ unlocked
                self.territory_controller._claim_log.is_locked(StationCode.BE),
                f"Territory BE locked early on claim {i}",
            )

            # attempt to claim BE, again
            self.territory_controller.claim_territory(StationCode.BE, Claimant.ZONE_0, 0)

        # assert BE locked
        self.assertTrue(
            self.territory_controller._claim_log.is_locked(StationCode.BE),
            f"Territory BE failed to lock after {LOCKED_OUT_AFTER_CLAIM} claims",
        )
