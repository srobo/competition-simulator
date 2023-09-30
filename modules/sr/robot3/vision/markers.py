from __future__ import annotations

import math

from sr.robot3.coordinates import vectors
from sr.robot3.coordinates.matrix import Matrix
from sr.robot3.coordinates.vectors import Vector

DEFAULT_SIZE = 1

NINETY_DEGREES = math.pi / 2
DEFAULT_ANGLE_TOLERANCE = math.radians(75)


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
        Rotate the token by the given rotation matrix.
        """
        self.corners = {
            name: matrix * position
            for name, position in self.corners.items()
        }

    def corners_global(self) -> dict[str, Vector]:
        """
        A mapping of the corners of the token (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the same origin as used to define the position of the token.
        """
        return {
            name: position + self.position
            for name, position in self.corners.items()
        }

    def normal(self) -> Vector:
        """
        A unit vector expressing the direction normal to the face of the token.
        """
        return vectors.unit_vector(sum(
            self.corners.values(),
            vectors.ZERO_3VECTOR,
        ))

    def top_midpoint(self) -> Vector:
        """
        The midpoint of the edge which the apparent marker on this face
        determines to be the "top" edge. It usually doesn't actually matter
        which edge this is, though in some games it does.
        """
        corners = [
            v for n, v in self.corners.items()
            if 'top' in n
        ]
        assert len(corners) == 2, "Wrong number of corners for 'top' edge"
        a, b = corners
        return (a + b) / 2
