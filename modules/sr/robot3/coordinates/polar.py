"""
Polar coordinate utilities.
"""

import math
from typing import NamedTuple

from .vectors import Vector


class PolarCoord(NamedTuple):
    length: float
    rot_x: float
    rot_y: float


def polar_from_cartesian(cartesian: Vector) -> PolarCoord:
    """
    Compute a `PolarCoord` representation of the given 3-vector compatible with
    libkoki's "bearing" object.

    Returned angles are in degrees.
    """
    if len(cartesian) != 3:
        raise ValueError(
            f"Can build polar coordinates for 3-vectors, not {cartesian!r}",
        )

    x, y, z = cartesian.data

    length = cartesian.magnitude()
    rot_y = math.atan2(x, z)
    rot_x = math.asin(y / length)

    return PolarCoord(
        length=length,
        rot_y=math.degrees(rot_y),
        rot_x=math.degrees(rot_x),
    )
