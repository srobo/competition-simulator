import math
import struct
from typing import Dict, NewType, Collection

# Webots specific library
from controller import Emitter, Receiver, Supervisor  # isort:skip

StationCode = NewType('StationCode', str)
Claimant = NewType('Claimant', int)

UNCLAIMED = Claimant(-1)

STATION_CODES: Collection[StationCode] = (
    StationCode('PN'),
    StationCode('EY'),
    StationCode('BE'),
    StationCode('PO'),
    StationCode('YL'),
    StationCode('BG'),
    StationCode('TS'),
    StationCode('OX'),
    StationCode('VB'),
    StationCode('SZ'),
    StationCode('SW'),
    StationCode('BN'),
    StationCode('HV'),
)

ZONE_COLOURS = ((0, 1, 0), (1, 0.375, 0))

RECEIVE_TICKS = 1

BROADCASTS_PER_SECOND = 10


class TerritoryController:

    _emitters: Dict[StationCode, Emitter]
    _receivers: Dict[StationCode, Receiver]

    def __init__(self) -> None:
        self._robot = Supervisor()
        self._station_statuses: Dict[StationCode, Claimant] = {
            code: UNCLAIMED for code in STATION_CODES
        }

    def setup(self) -> None:
        territory_controller.enable_receivers()
        self._emitters = {station_code: self._robot.getEmitter(station_code + "Emitter")
                          for station_code in STATION_CODES}

        self._receivers = {station_code: self._robot.getReceiver(station_code + "Receiver")
                           for station_code in STATION_CODES}

    def enable_receivers(self) -> None:
        for receiver in self._receivers.values():
            receiver.enable(RECEIVE_TICKS)

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

    def claim_territory(
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

    def process_packet(
        self,
        station_code: StationCode,
        packet: bytes,
        receive_time: float,
    ) -> None:
        try:
            robot_id, = struct.unpack("!B", packet)
            self.claim_territory(station_code, robot_id, self._robot.getTime())
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

    def transmit_pulses(self) -> None:
        for station_code, emitter in self._emitters.items():
            emitter.send(struct.pack("!2sb", str(station_code).encode('ASCII'),
                         self._station_statuses[station_code]))

    def main(self) -> None:
        territory_controller.setup()
        while True:
            self.receive_robot_captures()
            self.transmit_pulses()
            self.sleep(1 / BROADCASTS_PER_SECOND)


if __name__ == "__main__":
    territory_controller = TerritoryController()
    territory_controller.main()
