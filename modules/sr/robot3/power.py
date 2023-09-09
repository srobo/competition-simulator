from __future__ import annotations

import datetime
from enum import Enum
from typing import Union, Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from .robot import Robot


class Outputs(Enum):
    OUT_H0 = 'H0'
    OUT_H1 = 'H1'
    OUT_L0 = 'L0'
    OUT_L1 = 'L1'
    # OUT_L2 = 'L2' # Brain board runs from L2
    OUT_L3 = 'L3'
    OUT_FIVE_VOLT = 'FIVE_VOLT'


def init_power_board(robot: Robot) -> PowerBoard:
    return PowerBoard(robot)


class PowerBoard:
    def __init__(self, robot: Robot) -> None:
        self.outputs = OutputGroup()
        self.battery_sensor = BatterySensor()
        self.piezo = Piezo(robot)


class OutputGroup:
    def __init__(self) -> None:
        self._outputs = {x: Output() for x in Outputs}

    def power_on(self) -> None:
        for output in self._outputs.values():
            output.is_enabled = True

    def power_off(self) -> None:
        for output in self._outputs.values():
            output.is_enabled = False

    def __getitem__(self, index: Outputs) -> Output:
        return self._outputs[index]

    def __iter__(self) -> Iterator[Output]:
        return iter(self._outputs.values())

    def __len__(self) -> int:
        return len(self._outputs)


class Output:
    def __init__(self) -> None:
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @is_enabled.setter
    def is_enabled(self, enable: bool) -> None:
        self._enabled = enable

    @property
    def current(self) -> float:
        return 0.0


class BatterySensor:
    @property
    def voltage(self) -> float:
        return 12.0

    @property
    def current(self) -> float:
        return 0.0


class Piezo:
    def __init__(self, robot: Robot) -> None:
        self.robot = robot

    def buzz(
        self,
        duration: int | float | datetime.timedelta,
        pitch: Pitch,
        *,
        blocking: bool | None = None,
    ) -> None:
        if not blocking:
            return

        if isinstance(duration, datetime.timedelta):
            duration = duration.total_seconds()

        self.robot.sleep(duration)


class Note(float, Enum):
    """An enumeration of notes.
    An enumeration of notes from scientific pitch
    notation and their related frequencies in Hz.
    """

    C6 = 1047.0
    D6 = 1174.7
    E6 = 1318.5
    F6 = 1396.9
    G6 = 1568.0
    A6 = 1760.0
    B6 = 1975.5
    C7 = 2093.0
    D7 = 2349.3
    E7 = 2637.0
    F7 = 2793.8
    G7 = 3136.0
    A7 = 3520.0
    B7 = 3951.1
    C8 = 4186.0


Pitch = Union[int, float, Note]
