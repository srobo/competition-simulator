import enum
from typing import Dict, Mapping

import vectors
from matrix import Matrix
from vectors import Vector

TOKEN_SIZE = 1


class FaceName(enum.Enum):
    """
    Names of faces on a token in the reference position.

    As a token is rotated, the position of a named face also moves within space.
    That means that the "top" face of a token is not neccesarily the one called
    "Top".
    """

    Top = 'top'
    Bottom = 'bottom'

    Left = 'left'
    Right = 'right'

    Front = 'front'
    Rear = 'rear'


class Token:
    def __init__(self, position: Vector, size: float = TOKEN_SIZE) -> None:
        self.position = position
        self.corners = {
            'left-top-front': Vector((-1, 1, -1)) * size,
            'right-top-front': Vector((1, 1, -1)) * size,

            'left-bottom-front': Vector((-1, -1, -1)) * size,
            'right-bottom-front': Vector((1, -1, -1)) * size,

            'left-top-rear': Vector((-1, 1, 1)) * size,
            'right-top-rear': Vector((1, 1, 1)) * size,

            'left-bottom-rear': Vector((-1, -1, 1)) * size,
            'right-bottom-rear': Vector((1, -1, 1)) * size,
        }

    def rotate(self, matrix: Matrix) -> None:
        """
        Rotate the token by the given rotation matrix.
        """
        self.corners = {
            name: matrix * position
            for name, position in self.corners.items()
        }

    def face(self, name: FaceName) -> 'Face':
        """
        Get the named `Face` of the token.

        As a token is rotated, the position of a named face also moves within
        space. That means that the "top" face of a token is not neccesarily the
        one called "Top".
        """
        return Face(self, name)

    def corners_global(self) -> Dict[str, Vector]:
        """
        A mapping of the corners of the token (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the same origin as used to define the position of the token.
        """
        return {
            name: position + self.position
            for name, position in self.corners.items()
        }


class Face:
    def __init__(self, token: Token, name: FaceName) -> None:
        self.token = token
        self.name = name

    def _filter_corners(self, corners: Mapping[str, Vector]) -> Dict[str, Vector]:
        return {
            name: position
            for name, position in corners.items()
            if self.name.value in name
        }

    def corners(self) -> Dict[str, Vector]:
        """
        A mapping of the corners of the face (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the center of the token.
        """
        return self._filter_corners(self.token.corners)

    def corners_global(self) -> Dict[str, Vector]:
        """
        A mapping of the corners of the token (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the same origin as used to define the position of the token.
        """
        return self._filter_corners(self.token.corners_global())

    def normal(self) -> Vector:
        """
        A unit vector expressing the direction normal to the face of the token.
        """
        return vectors.unit_vector(sum(
            self.corners().values(),
            vectors.ZERO_3VECTOR,
        ))

    def centre(self) -> Vector:
        """
        The position of the centre of the face, relative to the token's centre.
        """
        corners = self.corners().values()
        assert len(corners) == 4
        normal = sum(corners, vectors.ZERO_3VECTOR)
        return normal / 4

    def centre_global(self) -> Vector:
        """
        The position of the centre of the face, relative to the origin used for
        the token's position.
        """
        return self.token.position + self.centre()

    def distance(self) -> float:
        """
        The distance to the centre of the face from the origin used for the
        token's position.
        """
        return self.centre_global().magnitude()

    def top_midpoint(self) -> Vector:
        """
        The midpoint of the edge which the apparent marker on this face
        determines to be the "top" edge. It usually doesn't actually matter
        which edge this is, though in some games it does.

        For faces which are not usually vertical, we pick the "rear" of the
        token to equate to be the place to put the "top" edge.
        This also matches how the markes were laid out in "Sunny Side Up".
        """
        if self.name in (FaceName.Top, FaceName.Bottom):
            corners = [
                v for n, v in self.corners().items()
                if FaceName.Rear.value in n
            ]
        else:
            corners = [
                v for n, v in self.corners().items()
                if FaceName.Top.value in n
            ]
        assert len(corners) == 2, "Wrong number of corners for 'top' edge"
        a, b = corners
        return (a + b) / 2
