import re
import sys
import unittest
from pathlib import Path

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'stubs'))

from territory_controller import (  # isort:skip
    Claimant,
    ClaimLog,
    StationCode,
    TerritoryRoot,
    TERRITORY_LINKS,
    AttachedTerritories,
)


class TestAttachedTerritories(unittest.TestCase):
    'Test build_attached_capture_trees/get_attached_territories'
    _zone_0_territories = {StationCode.BG, StationCode.TS, StationCode.OX,
                           StationCode.VB, StationCode.BE, StationCode.SZ}
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


class TestAdjacentTerritories(unittest.TestCase):
    'Test the AttachedTerritories initialisation of adjacent_zones'
    def setUp(self) -> None:
        super().setUp()
        claim_log = ClaimLog(record_arena_actions=False)
        self.attached_territories = AttachedTerritories(claim_log)

    def test_all_links_in_set(self) -> None:
        'test all territory links from Arena.wbt are in TERRITORY_LINKS'
        arena_links = set()
        for line in (REPO_ROOT / 'worlds' / 'Arena.wbt').open('r'):
            if re.search(r'SRLink', line):
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
