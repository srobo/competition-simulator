from __future__ import annotations

import math

from sr.robot3.coordinates import vectors
from sr.robot3.coordinates.matrix import Matrix
from sr.robot3.coordinates.vectors import Vector

DEFAULT_SIZE = 1

NINETY_DEGREES = math.pi / 2
DEFAULT_ANGLE_TOLERANCE = math.radians(80)


class FiducialMarker:
    """
    Represents a 2D fiducial marker which knows its position in space and can be
    rotated.

    Internally this stores its position in space separately from the positions
    of its corners, which are stored relative to the centre of the square that
    represents the marker.

    Instances of this type must have had their proper orientation applied in the
    world file.
    """

    def __init__(
        self,
        position: Vector,
        size: float = DEFAULT_SIZE,
    ) -> None:
        self.position = position

        # The dimensions here need to end up matching those passed to the marker
        # as defined in `protos/Markers/MarkerBase.proto`.

        thickness = 0.0001 / 2
        size = size / 2

        # Choose what Webots thinks of as the "rear" face -- the one nearer the
        # camera.
        offset = -thickness

        self.corners = {
            'top-left': Vector((offset, size, size)),
            'bottom-left': Vector((offset, size, -size)),

            'top-right': Vector((offset, -size, size)),
            'bottom-right': Vector((offset, -size, -size)),
        }

    def rotate(self, matrix: Matrix) -> None:
        """
        Rotate the marker by the given rotation matrix.
        """
        self.corners = {
            name: matrix * position
            for name, position in self.corners.items()
        }

    def corners_global(self) -> dict[str, Vector]:
        """
        A mapping of the corners of the marker (named for their apparent
        position on a reference marker) to the current position of that corner
        relative to the same origin as used to define the position of the
        marker.
        """
        return {
            name: position + self.position
            for name, position in self.corners.items()
        }

    def normal(self) -> Vector:
        """
        A unit vector expressing the direction normal to the marker.
        """
        return vectors.unit_vector(sum(
            self.corners.values(),
            vectors.ZERO_3VECTOR,
        ))

    def centre_global(self) -> Vector:
        """
        The position of the centre of the marker, relative to the same origin as
        used to define the general position of the marker.
        """
        corners = self.corners_global().values()
        assert len(corners) == 4
        normal = sum(corners, vectors.ZERO_3VECTOR)
        return normal / 4

    def angle_to_global_origin(self) -> float:
        direction_to_origin = -self.centre_global()
        normal = self.normal()
        return vectors.angle_between(direction_to_origin, normal)

    def is_visible_to_global_origin(
        self,
        angle_tolerance: float = DEFAULT_ANGLE_TOLERANCE,
    ) -> bool:
        if angle_tolerance > NINETY_DEGREES:
            raise ValueError(
                "Refusing to allow faces with angles > 90° to be visible "
                "(asked for {} radians, {})".format(
                    angle_tolerance,
                    math.degrees(angle_tolerance),
                ),
            )

        angle_to_origin = self.angle_to_global_origin()
        return abs(angle_to_origin) < angle_tolerance

    def top_midpoint(self) -> Vector:
        """
        The midpoint of the edge which the marker determines to be the "top"
        edge. It usually doesn't actually matter which edge this is, though in
        some games it does.
        """
        corners = [
            v for n, v in self.corners.items()
            if 'top' in n
        ]
        assert len(corners) == 2, "Wrong number of corners for 'top' edge"
        a, b = corners
        return (a + b) / 2
