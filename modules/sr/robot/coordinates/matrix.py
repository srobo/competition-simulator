"""
Matrix utilities.
"""
from typing import Tuple, Union, Iterable, overload

from .vectors import Vector


class Matrix:
    """
    An arbitrary size matrix of floating point values.

    In addition to the usual Python niceties, this supports scalar
    multiplication, matrix addition and vector multiplication (dot product).
    """

    def __init__(self, data: Iterable[Iterable[float]]) -> None:
        tuple_data = tuple(tuple(x) for x in data)

        lengths = set(len(x) for x in tuple_data)

        if len(lengths) != 1:
            raise ValueError(f"Malformed input to Matrix: {tuple_data!r}")

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
            raise ValueError(
                f"Dimension mismatch: cannot add {self.dimensions} to {other.dimensions}",
            )

        return Matrix(
            (x + y for x, y in zip(row_self, row_other))
            for row_self, row_other in zip(self.data, other.data)
        )

    def __sub__(self, other: 'Matrix') -> 'Matrix':
        if not isinstance(other, Matrix):
            return NotImplemented  # type: ignore[unreachable]

        return self.__add__(-other)

    @overload
    def __mul__(self, vector: Vector) -> Vector:
        ...

    @overload
    def __mul__(self, vector: Tuple[float, ...]) -> Tuple[float, ...]:
        ...

    def __mul__(
        self,
        vector: Union[Vector, Tuple[float, ...]],
    ) -> Union[Vector, Tuple[float, ...]]:
        if len(vector) != self.dimensions[1]:
            raise ValueError(
                f"Dimension mismatch: cannot multiply {self.dimensions} by {len(vector)}",
            )

        if isinstance(vector, Vector):
            data = vector.data
        else:
            data = vector

        values = (
            sum(x * y for x, y in zip(row_self, data))
            for row_self in self.data
        )

        if isinstance(vector, Vector):
            return Vector(values)
        else:
            return tuple(values)

    __rmul__ = __mul__

    def __matmul__(self, other: 'Matrix') -> 'Matrix':
        if not isinstance(other, Matrix):
            return NotImplemented  # type: ignore[unreachable]

        if self.dimensions != tuple(reversed(other.dimensions)):
            raise ValueError(
                f"Dimension mismatch: cannot multiply {self.dimensions} "
                "by {other.dimensions}",
            )

        return Matrix(
            (
                sum(x * y for x, y in zip(row_self, row_other))
                for row_other in other.transpose().data
            )
            for row_self in self.data
        )
