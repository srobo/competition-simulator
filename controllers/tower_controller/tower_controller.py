import math
import struct
from typing import Dict, NewType, Collection

# Webots specific library
from controller import Emitter, Receiver, Supervisor  # isort:skip

StationCode = NewType('StationCode', str)
Claimant = NewType('Claimant', int)

UNCLAIMED = Claimant(-1)

STATION_CODES: Collection[StationCode] = ('AB', 'CD', 'EF', 'GH')

ZONE_COLOURS = ((0, 1, 0), (1, 0.375, 0))

RECEIVE_TICKS = 1

BROADCASTS_PER_SECOND = 10


class TowerController:
    def __init__(self) -> None:
        self._robot = Supervisor()
        self._station_statuses: Dict[StationCode, Claimant] = {
            code: UNCLAIMED for code in STATION_CODES
        }

    def enable_receivers(self) -> None:
        for _, receiver in self.get_receivers().items():
            receiver.enable(RECEIVE_TICKS)

    def get_emitters(self) -> Dict[StationCode, Emitter]:
        return {station_code: self._robot.getEmitter(station_code + "Emitter")
                for station_code in STATION_CODES}

    def get_receivers(self) -> Dict[StationCode, Receiver]:
        return {station_code: self._robot.getReceiver(station_code + "Receiver")
                for station_code in STATION_CODES}

    def sleep(self, time_sec: float) -> None:
        time_step: int = int(self._robot.getBasicTimeStep())
        n_steps = math.ceil((time_sec * 1000) / time_step)
        duration_ms = n_steps * time_step
        self._robot.step(duration_ms)

    def _log_territory_claim(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        # TODO add better logging so we can score
        print(f"{station_code} CLAIMED BY {claimed_by} AT {claim_time}s")  # noqa:T001

    def claim_tower(
        self,
        station_code: StationCode,
        claimed_by: Claimant,
        claim_time: float,
    ) -> None:
        if self._station_statuses[station_code] == claimed_by:
            # This territory is already claimed by this claimant.
            return

        new_colour = ZONE_COLOURS[claimed_by]
        self._robot.getFromDef(station_code).getField("zoneColour").setSFColor(
            list(new_colour),
        )

        self._log_territory_claim(station_code, claimed_by, self._robot.getTime())
        self._station_statuses[station_code] = claimed_by

    def receive_robot_captures(self) -> None:
        receivers = self.get_receivers()
        for station_code, receiver in receivers.items():
            self.receive_tower(station_code, receiver)

    def process_packet(
        self,
        station_code: StationCode,
        packet: bytes,
        receive_time: float,
    ) -> None:
        try:
            robot_id, = struct.unpack("!B", packet)
            self.claim_tower(station_code, robot_id, self._robot.getTime())
        except ValueError:
            print(
                f"Received malformed packet at {receive_time} on {station_code}: {packet!r}",
            )   # noqa:T001

    def receive_tower(self, station_code: StationCode, receiver: Receiver) -> None:
        simulation_time = self._robot.getTime()

        while receiver.getQueueLength():
            try:
                data = receiver.getData()
                self.process_packet(station_code, data, simulation_time)
            finally:
                # Always advance to the next packet in queue: if there has been an exception,
                # it is safer to advance to the next.
                receiver.nextPacket()

    def transmit_pulses(self) -> None:
        emitters = self.get_emitters()
        for station_code, emitter in emitters.items():
            emitter.send(struct.pack("!2sb", str(station_code).encode('ASCII'),
                         self._station_statuses[station_code]))

    def main(self) -> None:
        tower_controller.enable_receivers()
        while True:
            self.receive_robot_captures()
            self.transmit_pulses()
            self.sleep(1 / BROADCASTS_PER_SECOND)


if __name__ == "__main__":
    tower_controller = TowerController()
    tower_controller.main()
