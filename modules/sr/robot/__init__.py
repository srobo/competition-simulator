import sr.robot._version_check  # noqa
from shared_utils import Owner, TargetInfo
from sr.robot.robot import Robot
from sr.robot.camera import (
    MarkerType,
    MARKER_ARENA,
    MARKER_TOKEN_GOLD,
    MARKER_TOKEN_SILVER,
)

__all__ = (
    'Robot',
    'Owner',
    'MarkerType',
    'TargetInfo',
    'MARKER_ARENA',
    'MARKER_TOKEN_GOLD',
    'MARKER_TOKEN_SILVER',
)
