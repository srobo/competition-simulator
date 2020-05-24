#!/usr/bin/env python

"""
Convert from Webots' (x, y, z, θ) axis-angle orientation to a slightly more
competitor-friendly format.
"""

import math
import argparse
from typing import Tuple, Union, Iterable, overload, NamedTuple

WebotsOrientation = NamedTuple('WebotsOrientation', (
    ('x', float),
    ('y', float),
    ('z', float),
    ('theta', float),
))


class Vector:
    def __init__(self, data: Iterable[float]) -> None:
        self.data = tuple(data)

    def magnitude(self) -> float:
        return math.sqrt(sum(x ** 2 for x in self.data))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented

        return self.data == other.data

    def __hash__(self) -> int:
        return hash(self.data)

    def __repr__(self) -> str:
        return 'Vector({!r})'.format(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __round__(self, precision: int) -> 'Vector':
        return Vector(round(x, precision) for x in self.data)

    def __neg__(self) -> 'Vector':
        return self * -1

    def __add__(self, other: 'Vector') -> 'Vector':
        if not isinstance(other, Vector):
            return NotImplemented  # type: ignore[unreachable]

        if len(self) != len(other):
            raise ValueError("Dimension mismatch: cannot add {} to {}".format(
                len(self),
                len(other),
            ))

        return Vector(x + y for x, y in zip(self.data, other.data))

    def __sub__(self, other: 'Vector') -> 'Vector':
        if not isinstance(other, Vector):
            return NotImplemented  # type: ignore[unreachable]

        return self.__add__(-other)

    @overload
    def __mul__(self, other: float) -> 'Vector':
        """
        Multiply vector by scalar.
        """
        ...

    @overload
    def __mul__(self, other: 'Vector') -> float:
        """
        Dot product between two vectors of equal length.

        Given vectors A and B, ``A · B == ||A|| ||B|| cos(theta)`` where
        theta is the angle between them.
        """
        ...

    def __mul__(self, value: 'Union[Vector, float]') -> 'Union[Vector, float]':
        if isinstance(value, (float, int)):
            return Vector(value * x for x in self.data)

        if not isinstance(value, Vector):
            return NotImplemented  # type: ignore[unreachable]

        if len(self) != len(value):
            raise ValueError("Dimension mismatch: cannot multiply {} by {}".format(
                len(self),
                len(value),
            ))

        return sum(x * y for x, y in zip(self.data, value.data))

    __rmul__ = __mul__


def cross_product(vec_a: Vector, vec_b: Vector) -> Vector:
    """
    Cross product of two vectors of equal length.

    Given vectors A and B, ``A × B == ||A|| ||B|| sin(theta)`` where
    theta is the angle between them.
    """
    a_x, a_y, a_z = vec_a.data
    b_x, b_y, b_z = vec_b.data

    return Vector((
        (a_y * b_z) - (a_z * b_y),
        (a_z * b_x) - (a_x * b_z),
        (a_x * b_y) - (a_y * b_x),
    ))


def dot_product(vec_a: Vector, vec_b: Vector) -> float:
    """
    Dot product between two vectors of equal length.

    Given vectors A and B, ``A · B == ||A|| ||B|| cos(theta)`` where
    theta is the angle between them.
    """
    return vec_a * vec_b


_ZERO_VECTOR = Vector((0, 0, 0))


def angle_between(vec_a: Vector, vec_b: Vector) -> float:
    """
    Determine the angle between two vectors, in degrees.

    This is calculated using the definition of the dot product and
    knowing the size of the vectors.
    """

    if len(vec_a) != 3 or len(vec_b) != 3:
        raise ValueError(
            "Can only find angle between three-dimensional vectors, not {!r} and {!r}".format(
                vec_a,
                vec_b,
            ),
        )

    if _ZERO_VECTOR in (vec_a, vec_b):
        raise ValueError("Cannot find the angle between an empty vector and another")

    dp = dot_product(vec_a, vec_b)
    mod_ab = vec_a.magnitude() * vec_b.magnitude()
    cos_theta = dp / mod_ab
    theta_rads = math.acos(cos_theta)
    theta_degrees = math.degrees(theta_rads)
    return theta_degrees


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


def rotation_matrix_from_axis_and_angle(orientation: WebotsOrientation) -> 'Matrix':
    x, y, z, theta = orientation

    # Seemingly webots' y is upside down versus Wikipedia's. Note: this also
    # changes the handedness of the axes.
    y *= -1

    size = round(x ** 2 + y ** 2 + z ** 2, 5)
    if size != 1:
        raise ValueError("Orientation vector {} is not a unit vector (length is {})".format(
            orientation[:3],
            size,
        ))

    cos_theta = math.cos(theta)
    one_minus_cos_theta = 1 - cos_theta
    sin_theta = math.sin(theta)

    x_sin_theta = x * sin_theta
    y_sin_theta = y * sin_theta
    z_sin_theta = z * sin_theta

    x_y_one_minus_cos_theta = x * y * one_minus_cos_theta
    x_z_one_minus_cos_theta = x * z * one_minus_cos_theta
    y_z_one_minus_cos_theta = y * z * one_minus_cos_theta

    # From https://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle
    return Matrix((
        (
            cos_theta + x ** 2 * one_minus_cos_theta,
            x_y_one_minus_cos_theta - z_sin_theta,
            x_z_one_minus_cos_theta + y_sin_theta,
        ),
        (
            x_y_one_minus_cos_theta + z_sin_theta,
            cos_theta + y ** 2 * one_minus_cos_theta,
            y_z_one_minus_cos_theta - x_sin_theta,
        ),
        (
            x_z_one_minus_cos_theta - y_sin_theta,
            y_z_one_minus_cos_theta + x_sin_theta,
            cos_theta + z ** 2 * one_minus_cos_theta,
        ),
    ))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('x')
    parser.add_argument('y')
    parser.add_argument('z')
    parser.add_argument('theta')
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    print(rotation_matrix_from_axis_and_angle(WebotsOrientation(
        args.x,
        args.y,
        args.z,
        args.theta,
    )))


if __name__ == '__main__':
    main(parse_args())
