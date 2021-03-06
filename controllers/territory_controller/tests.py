import re
import unittest
from pathlib import Path
from unittest.mock import patch

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
        StationCode.T3,
    }
    _zone_1_territories = {StationCode.PN, StationCode.EY, StationCode.PO, StationCode.YL}
    _zone_1_disconnected = {StationCode.PN, StationCode.EY}

    def load_territory_owners(self, claim_log: ClaimLog) -> None:
        # territories BG, TS, OX, VB, etc. owned by zone 0
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
        for station in {StationCode.YL, StationCode.PO, StationCode.T2}:
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
                StationCode.T3,
            },
            'Territory VB has incorrect territory links',
        )


class TestTerritoryLockout(unittest.TestCase):
    "Test that individual territories become 'locked' when claimed a set number of times"

    _zone_0_territories = {StationCode.PN, StationCode.EY}
    _zone_1_territories = {StationCode.YL, StationCode.PO}

    def assertLocked(self, station: StationCode, context: str) -> None:
        self.assertTrue(
            self.territory_controller._claim_log.is_locked(station),
            f"Territory {station.value} not locked {context}",
        )

    def assertNotLocked(self, station: StationCode, context: str) -> None:
        self.assertFalse(
            self.territory_controller._claim_log.is_locked(station),
            f"Territory {station.value} locked {context}",
        )

    def claim_territory(self, station_code: StationCode, claimed_by: Claimant) -> None:
        self.territory_controller.claim_territory(station_code, claimed_by, claim_time=0)

    def load_territory_owners(self, claim_log: ClaimLog) -> None:
        for territory in self._zone_0_territories:
            claim_log._station_statuses[territory] = Claimant.ZONE_0

        for territory in self._zone_1_territories:
            claim_log._station_statuses[territory] = Claimant.ZONE_1

    @patch('controller.Supervisor.getFromDef')
    @patch('territory_controller.get_robot_device')
    @patch('territory_controller.TerritoryController.set_score_display')
    def setUp(self, _: object, __: object, ___: object) -> None:
        super().setUp()
        claim_log = ClaimLog(record_arena_actions=False)
        self.load_territory_owners(claim_log)
        self.attached_territories = AttachedTerritories(claim_log)
        self.territory_controller = TerritoryController(
            claim_log,
            self.attached_territories,
        )

    @patch('controller.Supervisor.getFromDef')
    @patch('territory_controller.LOCKED_OUT_AFTER_CLAIM', new=2)
    @patch('territory_controller.TERRITORY_LINKS', new={
        (StationCode.PN, StationCode.EY),
        (TerritoryRoot.z0, StationCode.PN),
        (TerritoryRoot.z1, StationCode.PN),
    })
    def test_territory_lockout(self, _: object) -> None:
        """
        Test a territory is locked after the correct number of claims and
        disconnected territories aren't also locked.

        The reduce map in this test looks like this:

            z0 ── PN ── z1
                   └─ EY

        Thus EY is claimable only after PN has been claimed and can easily
        become unclaimed when PN is claimed. This test is validating both that
        PN becomes locked at the right point and also that EY does not become
        locked at that point.
        """

        self.claim_territory(StationCode.PN, Claimant.ZONE_0)
        self.claim_territory(StationCode.EY, Claimant.ZONE_0)

        self.assertNotLocked(StationCode.PN, "early after first claims")
        self.assertNotLocked(StationCode.EY, "early after first claims")

        self.claim_territory(StationCode.PN, Claimant.ZONE_1)
        self.claim_territory(StationCode.EY, Claimant.ZONE_1)

        self.assertNotLocked(StationCode.PN, "early after second claims")
        self.assertNotLocked(StationCode.EY, "early after second claims")

        self.claim_territory(StationCode.PN, Claimant.ZONE_0)

        self.assertLocked(StationCode.PN, "after third claim")
        self.assertNotLocked(StationCode.EY, "after lock-out of PN")

    @patch('controller.Supervisor.getFromDef')
    def test_self_lockout(self, _: object) -> None:
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
