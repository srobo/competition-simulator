import sr.robot._version_check  # noqa
from sr.robot.motor import BRAKE, COAST
from sr.robot.robot import Robot
from sr.robot.camera import (
    MarkerType,
    MARKER_ARENA,
    MARKER_TOKEN_GOLD,
    MARKER_TOKEN_SILVER,
)
from sr.robot.ruggeduino import INPUT, OUTPUT, INPUT_PULLUP

__all__ = (
    'OUTPUT',
    'INPUT',
    'INPUT_PULLUP',
    'COAST',
    'BRAKE',
    'Robot',
    'MarkerType',
    'MARKER_ARENA',
    'MARKER_TOKEN_GOLD',
    'MARKER_TOKEN_SILVER',
)
