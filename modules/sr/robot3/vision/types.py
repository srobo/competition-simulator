from __future__ import annotations

from typing import NamedTuple


class Orientation(NamedTuple):
    """
    Orientation of a marker in space.

    :param yaw:   Yaw of the marker, a rotation about the vertical axis, in radians.
                  Positive values indicate a rotation clockwise from the perspective
                  of the marker.
                  Zero values have the marker facing the camera square-on.
    :param pitch: Pitch of the marker, a rotation about the transverse axis, in
                  radians.
                  Positive values indicate a rotation upwards from the perspective
                  of the marker.
                  Zero values have the marker facing the camera square-on.
    :param roll:  Roll of the marker, a rotation about the longitudinal axis,
                  in radians.
                  Positive values indicate a rotation clockwise from the perspective
                  of the marker.
                  Zero values have the marker facing the camera square-on.
    """

    yaw: float
    pitch: float
    roll: float
