from enum import Enum
from typing import Union

from controller import Robot


class Outputs(Enum):
    OUT_H0 = 'H0'
    OUT_H1 = 'H1'
    OUT_L0 = 'L0'
    OUT_L1 = 'L1'
    OUT_L2 = 'L2'
    OUT_L3 = 'L3'


def init_power_board(webot: Robot) -> 'Power':
    return Power()


class Power:
    def __init__(self) -> None:
        output_array = [Output() for _ in Outputs]
        self.outputs = {
            key: value
            for key, value
            in zip(Outputs, output_array)
        }
        self.battery_sensor = BatterySensor()
        self.piezo = Piezo()

    def power_on(self) -> None:
        pass

    def power_off(self) -> None:
        pass


class Output:
    def __init__(self) -> None:
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @is_enabled.setter
    def enable_output(self, enable: bool) -> None:
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
    def buzz(self, duration: float, note: 'Pitch') -> None:
        pass


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
