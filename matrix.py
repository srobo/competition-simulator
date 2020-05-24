"""
Matrix utilities.
"""
from typing import Tuple, Iterable


class Matrix:
    def __init__(self, data: Iterable[Iterable[float]]) -> None:
        tuple_data = tuple(tuple(x) for x in data)

        lengths = set(len(x) for x in tuple_data)

        if len(lengths) != 1:
            raise ValueError("Malformed input to Matrix: {!r}".format(tuple_data))

        self.data = tuple_data

    @property
    def dimensions(self) -> Tuple[int, int]:
        return len(self.data), len(self.data[0])

    def transpose(self) -> 'Matrix':
        return Matrix(zip(*self.data))

    def __round__(self, precision: int) -> 'Matrix':
        return Matrix(
            (round(x, precision) for x in row)
            for row in self.data
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented

        return self.data == other.data

    def __hash__(self) -> int:
        return hash(self.data)

    def __repr__(self) -> str:
        return 'Matrix((\n    {},\n))'.format(
            ',\n    '.join(repr(x) for x in self.data),
        )

    def __neg__(self) -> 'Matrix':
        return Matrix((-x for x in row) for row in self.data)

    def __add__(self, other: 'Matrix') -> 'Matrix':
        if not isinstance(other, Matrix):
            return NotImplemented  # type: ignore[unreachable]

        if self.dimensions != other.dimensions:
            raise ValueError("Dimension mismatch: cannot add {} to {}".format(
                self.dimensions,
                other.dimensions,
            ))

        return Matrix(
            (x + y for x, y in zip(row_self, row_other))
            for row_self, row_other in zip(self.data, other.data)
        )

    def __sub__(self, other: 'Matrix') -> 'Matrix':
        if not isinstance(other, Matrix):
            return NotImplemented  # type: ignore[unreachable]

        return self.__add__(-other)

    def __mul__(self, vector: Tuple[float, ...]) -> Tuple[float, ...]:
        if len(vector) != self.dimensions[1]:
            raise ValueError("Dimension mismatch: cannot multiply {} by {}".format(
                self.dimensions,
                len(vector),
            ))

        return tuple(
            sum(x * y for x, y in zip(row_self, vector))
            for row_self in self.data
        )

    __rmul__ = __mul__

    def __matmul__(self, other: 'Matrix') -> 'Matrix':
        if not isinstance(other, Matrix):
            return NotImplemented  # type: ignore[unreachable]

        if self.dimensions != tuple(reversed(other.dimensions)):
            raise ValueError("Dimension mismatch: cannot multiply {} by {}".format(
                self.dimensions,
                other.dimensions,
            ))

        return Matrix(
            (
                sum(x * y for x, y in zip(row_self, row_other))
                for row_other in other.transpose().data
            )
            for row_self in self.data
        )
