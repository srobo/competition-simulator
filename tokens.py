import enum
from typing import Dict

import vectors
from matrix import Matrix
from vectors import Vector

TOKEN_SIZE = 1


class FaceName(enum.Enum):
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
        self.corners = {
            name: matrix * position
            for name, position in self.corners.items()
        }

    def face(self, name: FaceName) -> 'Face':
        return Face(self, name)


class Face:
    def __init__(self, token: Token, name: FaceName) -> None:
        self.token = token
        self.name = name

    def corners(self) -> Dict[str, Vector]:
        return {
            name: position
            for name, position in self.token.corners.items()
            if self.name.value in name
        }

    def normal(self) -> Vector:
        return vectors.unit_vector(sum(
            self.corners().values(),
            vectors.ZERO_3VECTOR,
        ))
