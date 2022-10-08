import sr.robot3._version_check  # noqa: F401
from sr.robot3.motor import BRAKE, COAST
from sr.robot3.power import Note, Outputs
from sr.robot3.robot import Robot
from sr.robot3.camera import (
    MarkerType,
    MARKER_ARENA,
    MARKER_TOKEN_GOLD,
    MARKER_TOKEN_SILVER,
)
from sr.robot3.ruggeduino import INPUT, OUTPUT, AnaloguePin, INPUT_PULLUP

OUT_H0 = Outputs.OUT_H0
OUT_H1 = Outputs.OUT_H1
OUT_L0 = Outputs.OUT_L0
OUT_L1 = Outputs.OUT_L1
OUT_L2 = Outputs.OUT_L2
OUT_L3 = Outputs.OUT_L3

A0 = AnaloguePin.A0
A1 = AnaloguePin.A1
A2 = AnaloguePin.A2
A3 = AnaloguePin.A3
A4 = AnaloguePin.A4
A5 = AnaloguePin.A5


__all__ = (
    'OUTPUT',
    'INPUT',
    'INPUT_PULLUP',
    'COAST',
    'BRAKE',
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
    'OUT_L2',
    'OUT_L3',
    'MarkerType',
    'MARKER_ARENA',
    'MARKER_TOKEN_GOLD',
    'MARKER_TOKEN_SILVER',
)
