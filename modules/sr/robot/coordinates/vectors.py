"""
Vector utilities.
"""
from __future__ import annotations

import math
from typing import Union, Iterable, overload

# between vectors considered the same
DEGREES_TOLERANCE = 10


class Vector:
    """
    An arbitrary length vector of floating point values.

    In addition to the usual Python niceties, this supports scalar
    multiplication & division, vector addition and vector multiplication (dot
    product).
    """

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
        return f'Vector({self.data!r})'

    def __len__(self) -> int:
        return len(self.data)

    def __round__(self, precision: int) -> Vector:
        return Vector(round(x, precision) for x in self.data)

    def __neg__(self) -> Vector:
        return self * -1

    def __add__(self, other: Vector) -> Vector:
        if not isinstance(other, Vector):
            return NotImplemented  # type: ignore[unreachable]

        if len(self) != len(other):
            raise ValueError(f"Dimension mismatch: cannot add {len(self)} to {len(other)}")

        return Vector(x + y for x, y in zip(self.data, other.data))

    def __sub__(self, other: Vector) -> Vector:
        if not isinstance(other, Vector):
            return NotImplemented  # type: ignore[unreachable]

        return self.__add__(-other)

    @overload
    def __mul__(self, other: float) -> Vector:
        """
        Multiply vector by scalar.
        """
        ...

    @overload
    def __mul__(self, other: Vector) -> float:
        """
        Dot product between two vectors of equal length.

        Given vectors A and B, ``A · B == ||A|| ||B|| cos(theta)`` where
        theta is the angle between them.
        """
        ...

    def __mul__(self, value: Union[Vector, float]) -> Union[Vector, float]:
        if isinstance(value, (float, int)):
            return Vector(value * x for x in self.data)

        if not isinstance(value, Vector):
            return NotImplemented  # type: ignore[unreachable]

        if len(self) != len(value):
            raise ValueError(
                f"Dimension mismatch: cannot multiply {len(self)} by {len(value)}",
            )

        return sum(x * y for x, y in zip(self.data, value.data))

    __rmul__ = __mul__

    def __truediv__(self, other: float) -> Vector:
        if not isinstance(other, (float, int)):
            return NotImplemented  # type: ignore[unreachable]

        return Vector(x / other for x in self.data)


def cross_product(vec_a: Vector, vec_b: Vector) -> Vector:
    """
    Cross product of two 3-vectors.

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
    Dot product between two vectors of equal size.

    Given vectors A and B, ``A · B == ||A|| ||B|| cos(theta)`` where
    theta is the angle between them.
    """
    return vec_a * vec_b


ZERO_3VECTOR = Vector((0, 0, 0))


def angle_between(vec_a: Vector, vec_b: Vector) -> float:
    """
    Determine the angle between two vectors, in degrees.

    This is calculated using the definition of the dot product and
    knowing the size of the vectors.
    """

    if len(vec_a) != 3 or len(vec_b) != 3:
        raise ValueError(
            "Can only find angle between three-dimensional vectors, "
            f"not {vec_a!r} and {vec_b!r}",
        )

    if ZERO_3VECTOR in (vec_a, vec_b):
        raise ValueError("Cannot find the angle between an empty vector and another")

    dp = dot_product(vec_a, vec_b)
    mod_ab = vec_a.magnitude() * vec_b.magnitude()
    cos_theta = dp / mod_ab

    if abs(cos_theta) > 1:
        # Round small floating point rounding errors to avoid a math domain
        # error from math.acos, without masking genuine errors.
        cos_theta = round(cos_theta, 15)

    theta_rads = math.acos(cos_theta)
    theta_degrees = math.degrees(theta_rads)
    return theta_degrees


def are_same_direction(vec_a: Vector, vec_b: Vector) -> bool:
    if ZERO_3VECTOR in (vec_a, vec_b):
        return False

    theta = angle_between(vec_a, vec_b)
    return theta < DEGREES_TOLERANCE


def unit_vector(direction_vector: Vector) -> Vector:
    magnitude = direction_vector.magnitude()
    if not magnitude:
        return direction_vector

    return direction_vector / magnitude
