import sr.robot._version_check  # noqa
from sr.robot.arduino import AnalougePin
from sr.robot.radio import Claimant, StationCode
from sr.robot.robot import Robot
from sr.robot.camera import (
    MarkerType,
    MARKER_ARENA,
    MARKER_TOKEN_GOLD,
    MARKER_TOKEN_SILVER,
)

__all__ = (
    'Robot',
    'AnalougePin',
    'Claimant',
    'MarkerType',
    'StationCode',
    'MARKER_ARENA',
    'MARKER_TOKEN_GOLD',
    'MARKER_TOKEN_SILVER',
)
