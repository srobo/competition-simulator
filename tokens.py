import enum
from typing import Dict

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
    def __init__(self, size: float = TOKEN_SIZE) -> None:
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


class Face:
    def __init__(self, token: Token, name: FaceName) -> None:
        self.token = token
        self.name = name

    def corners(self) -> Dict[str, Vector]:
        """
        A mapping of the corners of the face (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the center of the token.
        """
        return {
            name: position
            for name, position in self.token.corners.items()
            if self.name.value in name
        }

    def normal(self) -> Vector:
        """
        A unit vector expressing the direction normal to the face of the token.
        """
        return vectors.unit_vector(sum(
            self.corners().values(),
            vectors.ZERO_3VECTOR,
        ))
