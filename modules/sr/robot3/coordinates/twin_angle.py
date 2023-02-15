"""
Polar coordinate utilities.
"""

from __future__ import annotations

import math
from typing import NamedTuple

from .vectors import Vector


class Spherical(NamedTuple):
    """
    Analogue of zoloto's twin-angle `Spherical` type.

    This is not the traditional spherical coordinates mechanism and as such
    there are coordinates it cannot distinguish between. However it's what the
    API uses, so we match that.
    """

    rot_x: float
    rot_y: float
    dist: int

    @property
    def distance(self) -> int:
        return self.dist


def spherical_from_cartesian(cartesian: Vector) -> Spherical:
    """
    Compute a `Spherical` representation of the given 3-vector compatible with
    Zoloto's.

    Returned angles are in radians.
    """
    if len(cartesian) != 3:
        raise ValueError(
            f"Can build spherical coordinates for 3-vectors, not {cartesian!r}",
        )

    x, y, z = cartesian.data

    length = cartesian.magnitude()
    rot_x = math.atan2(y, z)
    rot_y = math.atan2(x, z)

    return Spherical(
        rot_y=rot_y,
        rot_x=rot_x,
        dist=int(length),
    )
