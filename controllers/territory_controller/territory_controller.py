import sys
import enum
import struct
from typing import Dict, List, Tuple
from pathlib import Path

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


# Updating? Update `Arena.wbt` too
ZONE_COLOURS = ((1, 0, 1), (1, 1, 0))


class ClaimLog:
    def __init__(self, record_arena_actions: bool) -> None:
        self._record_arena_actions = record_arena_actions

        self._station_statuses: Dict[StationCode, Claimant] = {
            code: Claimant.UNCLAIMED for code in StationCode
        }

        self._log: List[Tuple[StationCode, Claimant, float]] = []
        # Starting with a dirty log ensures the structure is written for every match.
        self._log_is_dirty = True

    def get_claimant(self, station_code: StationCode) -> Claimant:
        return self._station_statuses[station_code]

    def log_territory_claim(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        self._log.append((station_code, claimed_by, claim_time))
        self._log_is_dirty = True
        print(f"{station_code} CLAIMED BY {claimed_by} AT {claim_time}s")  # noqa:T001
        self._station_statuses[station_code] = claimed_by

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


class TerritoryController:

    _emitters: Dict[StationCode, Emitter]
    _receivers: Dict[StationCode, Receiver]

    def __init__(self, claim_log: ClaimLog) -> None:
        self._claim_log = claim_log
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

    def claim_territory(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        if self._claim_log.get_claimant(station_code) == claimed_by:
            # This territory is already claimed by this claimant.
            return

        new_colour = ZONE_COLOURS[claimed_by]
        station = self._robot.getFromDef(station_code)
        if station is None:
            raise RuntimeError(
                f"Failed to fetch territory node {station_code}",
            )
        station.getField("zoneColour").setSFColor(
            list(new_colour),
        )

        self._claim_log.log_territory_claim(station_code, claimed_by, self._robot.getTime())

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

    def receive_robot_captures(self) -> None:
        for station_code, receiver in self._receivers.items():
            self.receive_territory(station_code, receiver)

        self._claim_log.record_captures()

    def transmit_pulses(self) -> None:
        for station_code, emitter in self._emitters.items():
            emitter.send(struct.pack("!2sb", station_code.encode('ASCII'),
                         int(self._claim_log.get_claimant(station_code))))

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
    territory_controller = TerritoryController(claim_log)
    territory_controller.main()
