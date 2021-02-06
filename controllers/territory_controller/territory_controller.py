import sys
import enum
import struct
import logging
from typing import Set, Dict, List, Tuple, Union
from pathlib import Path
from collections import defaultdict

# Webots specific library
from controller import Emitter, Receiver, Supervisor

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

import controller_utils  # isort:skip
from sr.robot.utils import get_robot_device  # isort:skip

RECEIVE_TICKS = 1

# Updating? Update radio.py too.
BROADCASTS_PER_SECOND = 10


# Updating? Update radio.py too.
class Claimant(enum.IntEnum):
    UNCLAIMED = -1
    ZONE_0 = 0
    ZONE_1 = 1


LOCKED_OUT_AFTER_CLAIM = 4


# Updating? Update radio.py too.
class StationCode(str, enum.Enum):
    PN = 'PN'
    EY = 'EY'
    BE = 'BE'
    PO = 'PO'
    YL = 'YL'
    BG = 'BG'
    TS = 'TS'
    OX = 'OX'
    VB = 'VB'
    SZ = 'SZ'
    SW = 'SW'
    BN = 'BN'
    HV = 'HV'


class TerritoryRoot(str, enum.Enum):
    z0 = 'z0'
    z1 = 'z1'


# Updating? Update `Arena.wbt` too
ZONE_COLOURS: Dict[Claimant, Tuple[float, float, float]] = {
    Claimant.ZONE_0: (1, 0, 1),
    Claimant.ZONE_1: (1, 1, 0),
    Claimant.UNCLAIMED: (0.34191456, 0.34191436, 0.34191447),
}

LINK_COLOURS: Dict[Claimant, Tuple[float, float, float]] = {
    Claimant.ZONE_0: (0.5, 0, 0.5),
    Claimant.ZONE_1: (0.6, 0.6, 0),
    Claimant.UNCLAIMED: (0.25, 0.25, 0.25),
}

LOCKED_COLOUR = (0.5, 0, 0)

TERRITORY_LINKS: Set[Tuple[Union[StationCode, TerritoryRoot], StationCode]] = {
    (StationCode.PN, StationCode.EY),  # PN-EY
    (StationCode.BG, StationCode.OX),  # BG-OX
    (StationCode.OX, StationCode.TS),  # OX-TS
    (StationCode.TS, StationCode.VB),  # TS-VB
    (StationCode.EY, StationCode.BE),  # EY-BE
    (StationCode.VB, StationCode.BE),  # VB-BE
    (StationCode.VB, StationCode.SZ),  # VB-SZ
    (StationCode.BE, StationCode.SZ),  # BE-SZ
    (StationCode.BE, StationCode.PO),  # BE-PO
    (StationCode.SZ, StationCode.SW),  # SZ-SW
    (StationCode.PO, StationCode.YL),  # PO-YL
    (StationCode.SW, StationCode.BN),  # SW-BN
    (StationCode.HV, StationCode.BN),  # HV-BN
    # These links are between territories and the starting zones
    (TerritoryRoot.z0, StationCode.PN),  # z0-PN
    (TerritoryRoot.z0, StationCode.TS),  # z0-TS
    (TerritoryRoot.z0, StationCode.BG),  # z0-BG
    (TerritoryRoot.z1, StationCode.YL),  # z1-YL
    (TerritoryRoot.z1, StationCode.SW),  # z1-SW
    (TerritoryRoot.z1, StationCode.HV),  # z1-HV
}


ClaimLogEntry = Tuple[StationCode, Claimant, float, bool]


class ClaimLog:
    def __init__(self, record_arena_actions: bool) -> None:
        self._record_arena_actions = record_arena_actions

        self._station_statuses: Dict[StationCode, Claimant] = {
            code: Claimant.UNCLAIMED for code in StationCode
        }
        self._locked_territories: Set[StationCode] = set()

        self._log: List[ClaimLogEntry] = []
        # Starting with a dirty log ensures the structure is written for every match.
        self._log_is_dirty = True

    def get_claimant(self, station_code: StationCode) -> Claimant:
        return self._station_statuses[station_code]

    def is_locked(self, station_code: StationCode) -> bool:
        return station_code in self._locked_territories

    def get_claim_count(self, station_code: StationCode) -> int:
        return len([x for x, _, _, _ in self._log if x == station_code])

    def _record_log_entry(self, entry: ClaimLogEntry) -> None:
        self._log.append(entry)
        self._log_is_dirty = True

    def log_territory_claim(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        self._record_log_entry((station_code, claimed_by, claim_time, False))
        print(f"{station_code} CLAIMED BY {claimed_by.name} AT {claim_time}s")  # noqa:T001
        self._station_statuses[station_code] = claimed_by

    def log_lock(
        self,
        station_code: StationCode,
        locked_by: Claimant,
        claim_time: float,
    ) -> None:
        self._record_log_entry((station_code, Claimant.UNCLAIMED, claim_time, True))
        print(f"{station_code} LOCKED OUT BY {locked_by.name} at {claim_time}s")  #noqa:T001
        self._station_statuses[station_code] = Claimant.UNCLAIMED
        self._locked_territories.add(station_code)

    def record_captures(self) -> None:
        if not self._record_arena_actions:
            return

        if not self._log_is_dirty:
            # Don't write the log if nothing new has happened.
            return

        controller_utils.record_arena_data({'territory_claims': [
            {
                'zone': claimed_by.value,
                'station_code': station_code.value,
                'time': claim_time,
            }
            for station_code, claimed_by, claim_time in self._log
        ]})

        self._log_is_dirty = False

    def is_dirty(self) -> bool:
        return self._log_is_dirty


class AttachedTerritories:
    def __init__(self, claim_log: ClaimLog):
        self._claim_log = claim_log
        self.adjacent_zones = self.calculate_adjacent_territories()

    def calculate_adjacent_territories(
        self,
    ) -> Dict[Union[StationCode, TerritoryRoot], Set[StationCode]]:
        adjacent_zones: Dict[
            Union[StationCode, TerritoryRoot],
            Set[StationCode],
        ] = defaultdict(set)

        for source, dest in TERRITORY_LINKS:
            adjacent_zones[source].add(dest)

            # Links with stations at both ends are reversable, but links from
            # starting zones are only usefully considered in one direction.
            if isinstance(source, StationCode):
                adjacent_zones[dest].add(source)

        return adjacent_zones

    def get_attached_territories(
        self,
        station_code: Union[StationCode, TerritoryRoot],
        claimant: Claimant,
        claimed_stations: Set[StationCode],
    ) -> None:
        for station in self.adjacent_zones[station_code]:
            if self._claim_log.get_claimant(station) != claimant:
                # adjacent territory has different owner
                continue
            if station in claimed_stations:
                # another path already connects this station
                continue
            # add this station before recursing to prevent
            # looping through mutually connected nodes
            claimed_stations.add(station)
            self.get_attached_territories(station, claimant, claimed_stations)

    def build_attached_capture_trees(self) -> Tuple[Set[StationCode], Set[StationCode]]:
        zone_0_territories: Set[StationCode] = set()
        zone_1_territories: Set[StationCode] = set()

        # the territory lists are passed by reference and populated by the functions
        self.get_attached_territories(TerritoryRoot.z0, Claimant.ZONE_0, zone_0_territories)
        self.get_attached_territories(TerritoryRoot.z1, Claimant.ZONE_1, zone_1_territories)
        return (zone_0_territories, zone_1_territories)

    def can_capture_station(
        self,
        station_code: StationCode,
        attempting_claim: Claimant,
        connected_territories: Tuple[Set[StationCode], Set[StationCode]],
    ) -> bool:
        if attempting_claim == Claimant.UNCLAIMED:
            # This condition shouldn't occur and
            # we don't track adjacency for unclaimed territories
            return True

        for station in self.adjacent_zones[station_code]:
            if station in connected_territories[attempting_claim]:
                # an adjacent territory has a connection back to the robot's starting zone
                return True

        if station_code in self.adjacent_zones[TerritoryRoot(f'z{attempting_claim.value}')]:
            # robot is capturing a zone directly connected to it's starting zone
            return True

        return False


class TerritoryController:

    _emitters: Dict[StationCode, Emitter]
    _receivers: Dict[StationCode, Receiver]

    def __init__(self, claim_log: ClaimLog, attached_territories: AttachedTerritories) -> None:
        self._claim_log = claim_log
        self._attached_territories = attached_territories
        self._robot = Supervisor()
        self._claim_starts: Dict[Tuple[StationCode, Claimant], float] = {}

        self._emitters = {
            station_code: get_robot_device(self._robot, station_code + "Emitter", Emitter)
            for station_code in StationCode
        }

        self._receivers = {
            station_code: get_robot_device(self._robot, station_code + "Receiver", Receiver)
            for station_code in StationCode
        }

        for receiver in self._receivers.values():
            receiver.enable(RECEIVE_TICKS)

    def begin_claim(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        self._claim_starts[station_code, claimed_by] = claim_time

    def has_begun_claim_in_time_window(
        self,
        station_code: StationCode,
        claimant: Claimant,
        current_time: float,
    ) -> bool:
        try:
            start_time = self._claim_starts[station_code, claimant]
        except KeyError:
            return False
        time_delta = current_time - start_time
        return 1.8 <= time_delta <= 2.1

    def set_territory_ownership(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        if self._claim_log.is_locked(station_code):
            logging.error(
                f"Territory {station_code} is locked",
            )
            return

        station = self._robot.getFromDef(station_code)
        if station is None:
            logging.error(
                f"Failed to fetch territory node {station_code}",
            )
            return

        if self._claim_log.get_claim_count(station_code) == LOCKED_OUT_AFTER_CLAIM - 1:
            # This next claim would trigger the "locked out" condition, so rather than
            # making the claim, instead cause a lock-out.
            station.getField("zoneColour").setSFColor(list(LOCKED_COLOUR))

            self._claim_log.log_lock(station_code, claimed_by, self._robot.getTime())

        else:
            new_colour = ZONE_COLOURS[claimed_by]

            station.getField("zoneColour").setSFColor(list(new_colour))

            self._claim_log.log_territory_claim(
                station_code,
                claimed_by,
                self._robot.getTime(),
            )

    def prune_detached_stations(
        self,
        connected_territories: Tuple[Set[StationCode], Set[StationCode]],
        claim_time: float,
    ) -> None:
        # find territories which lack connections back to their claimant's corner
        for station in StationCode:  # for territory in station_codes
            if self._claim_log.get_claimant(station) == Claimant.UNCLAIMED:
                # unclaimed territories can't be pruned
                continue

            if station in connected_territories[0]:
                # territory is linked back to zone 0's starting corner
                continue

            if station in connected_territories[1]:
                # territory is linked back to zone 1's starting corner
                continue

            # all disconnected territory is unclaimed
            self.set_territory_ownership(station, Claimant.UNCLAIMED, claim_time)

    def claim_territory(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        connected_territories = self._attached_territories.build_attached_capture_trees()

        if not self._attached_territories.can_capture_station(
            station_code,
            claimed_by,
            connected_territories,
        ):
            # This claimant doesn't have a connection back to their starting zone
            print(f"Robot in zone {claimed_by} failed to capture {station_code}")  # noqa: T001
            return

        self.set_territory_ownership(station_code, claimed_by, claim_time)

        # recalculate connected territories to account for
        # the new capture and newly created islands
        connected_territories = self._attached_territories.build_attached_capture_trees()

        self.prune_detached_stations(connected_territories, claim_time)

    def process_packet(
        self,
        station_code: StationCode,
        packet: bytes,
        receive_time: float,
    ) -> None:
        try:
            robot_id, is_conclude = struct.unpack("!BB", packet)  # type: Tuple[int, int]
            claimant = Claimant(robot_id)
            if is_conclude:
                if self.has_begun_claim_in_time_window(
                    station_code,
                    claimant,
                    receive_time,
                ):
                    self.claim_territory(
                        station_code,
                        claimant,
                        receive_time,
                    )
            else:
                self.begin_claim(
                    station_code,
                    claimant,
                    receive_time,
                )
        except ValueError:
            print(  # noqa:T001
                f"Received malformed packet at {receive_time} on {station_code}: {packet!r}",
            )

    def receive_territory(self, station_code: StationCode, receiver: Receiver) -> None:
        simulation_time = self._robot.getTime()

        while receiver.getQueueLength():
            try:
                data = receiver.getData()
                self.process_packet(station_code, data, simulation_time)
            finally:
                # Always advance to the next packet in queue: if there has been an exception,
                # it is safer to advance to the next.
                receiver.nextPacket()

    def update_territory_links(self) -> None:
        for stn_a, stn_b in TERRITORY_LINKS:
            if isinstance(stn_a, TerritoryRoot):  # starting zone is implicitly owned
                if stn_a == TerritoryRoot.z0:
                    stn_a_claimant = Claimant.ZONE_0
                else:
                    stn_a_claimant = Claimant.ZONE_1
            else:
                stn_a_claimant = self._claim_log.get_claimant(stn_a)

            stn_b_claimant = self._claim_log.get_claimant(stn_b)

            # if both ends are owned by the same Claimant
            if stn_a_claimant == stn_b_claimant:
                claimed_by = stn_a_claimant
            else:
                claimed_by = Claimant.UNCLAIMED

            new_colour = LINK_COLOURS[claimed_by]
            visual_link = self._robot.getFromDef('-'.join((stn_a, stn_b)))
            if visual_link is None:
                logging.error(
                    f"Failed to fetch territory link {visual_link}",
                )
            else:
                visual_link.getField("zoneColour").setSFColor(
                    list(new_colour),
                )

    def receive_robot_captures(self) -> None:
        for station_code, receiver in self._receivers.items():
            self.receive_territory(station_code, receiver)

        if self._claim_log.is_dirty():
            self.update_territory_links()

        self._claim_log.record_captures()

    def transmit_pulses(self) -> None:
        for station_code, emitter in self._emitters.items():
            emitter.send(
                struct.pack(
                    "!2sbb",
                    station_code.encode("ASCII"),
                    int(self._claim_log.get_claimant(station_code)),
                    int(self._claim_log.is_locked(station_code)),
                ),
            )

    def main(self) -> None:
        timestep = self._robot.getBasicTimeStep()
        steps_per_broadcast = (1 / BROADCASTS_PER_SECOND) / (timestep / 1000)
        counter = 0
        while True:
            counter += 1
            self.receive_robot_captures()
            if counter > steps_per_broadcast:
                self.transmit_pulses()
                counter = 0
            self._robot.step(int(timestep))


if __name__ == "__main__":
    claim_log = ClaimLog(record_arena_actions=(
        controller_utils.get_match_file().exists() and
        controller_utils.get_robot_mode() == 'comp'
    ))
    attached_territories = AttachedTerritories(claim_log)
    territory_controller = TerritoryController(claim_log, attached_territories)
    territory_controller.main()
