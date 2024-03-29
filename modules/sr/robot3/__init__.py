import sr.robot3._version_check  # noqa: F401
from sr.robot3.motor import BRAKE, COAST
from sr.robot3.power import Note, Outputs
from sr.robot3.robot import Robot
from sr.robot3.arduino import AnaloguePin
from sr.robot3.metadata import RobotMode
from sr.robot3.arduino_devices import GPIOPinMode

OUT_H0 = Outputs.OUT_H0
OUT_H1 = Outputs.OUT_H1
OUT_L0 = Outputs.OUT_L0
OUT_L1 = Outputs.OUT_L1
OUT_L3 = Outputs.OUT_L3
OUT_FIVE_VOLT = Outputs.OUT_FIVE_VOLT

A0 = AnaloguePin.A0
A1 = AnaloguePin.A1
A2 = AnaloguePin.A2
A3 = AnaloguePin.A3
A4 = AnaloguePin.A4
A5 = AnaloguePin.A5

# Match kit spelling. TODO: drop this once the kit has fixed the spelling.  # noqa: T101
AnalogPins = AnaloguePin

COMP = RobotMode.COMP
DEV = RobotMode.DEV

OUTPUT = GPIOPinMode.OUTPUT
INPUT = GPIOPinMode.INPUT
INPUT_PULLUP = GPIOPinMode.INPUT_PULLUP


__all__ = (
    'OUTPUT',
    'INPUT',
    'INPUT_PULLUP',
    'COAST',
    'BRAKE',
    'COMP',
    'DEV',
    'Robot',
    'Note',
    'A0',
    'A1',
    'A2',
    'A3',
    'A4',
    'A5',
    'OUT_H0',
    'OUT_H1',
    'OUT_L0',
    'OUT_L1',
    'OUT_L3',
    'OUT_FIVE_VOLT',
)
