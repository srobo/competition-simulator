from matrix import Matrix
from vectors import Vector

TOKEN_SIZE = 1


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
