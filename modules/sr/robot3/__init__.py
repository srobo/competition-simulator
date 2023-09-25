import sr.robot3._version_check  # noqa: F401
from sr.robot3.motor import BRAKE, COAST
from sr.robot3.power import Note, Outputs
from sr.robot3.robot import Robot
from sr.robot3.arduino import AnalogPins, GPIOPinMode
from sr.robot3.metadata import RobotMode

OUT_H0 = Outputs.OUT_H0
OUT_H1 = Outputs.OUT_H1
OUT_L0 = Outputs.OUT_L0
OUT_L1 = Outputs.OUT_L1
OUT_L3 = Outputs.OUT_L3
OUT_FIVE_VOLT = Outputs.OUT_FIVE_VOLT

A0 = AnalogPins.A0
A1 = AnalogPins.A1
A2 = AnalogPins.A2
A3 = AnalogPins.A3
A4 = AnalogPins.A4
A5 = AnalogPins.A5
A6 = AnalogPins.A6
A7 = AnalogPins.A7

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
    'A6',
    'A7',
    'OUT_H0',
    'OUT_H1',
    'OUT_L0',
    'OUT_L1',
    'OUT_L3',
    'OUT_FIVE_VOLT',
)
