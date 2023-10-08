"""
Coordinate types based on twin angles.

These types are similar to traditional spherical coordinates, however differ due
to the two angles being independent from one another.
"""

from __future__ import annotations

import math
from typing import NamedTuple


class Position(NamedTuple):
    """
    Position of a marker in space from the camera's perspective.

    :param distance:          Distance from the camera to the marker, in millimetres.
    :param horizontal_angle:  Horizontal angle from the camera to the marker, in radians.
                              Ranges from -pi to pi, with positive values indicating
                              markers to the right of the camera. Directly in front
                              of the camera is 0 rad.
    :param vertical_angle:    Vertical angle from the camera to the marker, in radians.
                              Ranges from -pi to pi, with positive values indicating
                              markers above the camera. Directly in front of the camera
                              is 0 rad.
    """

    distance: float
    horizontal_angle: float
    vertical_angle: float

    @classmethod
    def from_cartesian_metres(cls, cartesian: tuple[float, float, float]) -> Position:
        """
        Construct an instance given a cartesian position expressed in metres.

        The expected cartesian coordinate systems is:
        - x: distance away from the camera
        - y: distance left of the camera
        - z: distance above the camera

        See https://github.com/srobo/sr-robot/blob/a1c7d2e5f21d1d482d2b2ff1d99110865ecb392e/sr/robot3/marker.py#L145-L148
        """  # noqa: E501
        x, y, z = cartesian

        # From https://github.com/srobo/sr-robot/blob/a1c7d2e5f21d1d482d2b2ff1d99110865ecb392e/sr/robot3/marker.py#L127-L131  # noqa: E501
        return cls(
            distance=int(math.hypot(*cartesian) * 1000),
            horizontal_angle=math.atan2(-y, x),
            vertical_angle=math.atan2(z, x),
        )
