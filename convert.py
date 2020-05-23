#!/usr/bin/env python

"""
Convert from Webots' (x, y, z, θ) axis-angle orientation to a slightly more
competitor-friendly format.
"""

import math
import argparse
from typing import Tuple, Union, Iterable, overload, NamedTuple

from typing_extensions import Literal

WebotsOrientation = NamedTuple('WebotsOrientation', (
    ('x', float),
    ('y', float),
    ('z', float),
    ('theta', float),
))

NormalisedVector = NamedTuple('NormalisedVector', (
    ('x', float),
    ('y', float),
    ('z', float),
))

ThreeFloats = Tuple[float, float, float]


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

    def round(self, precision: int) -> 'Matrix':
        return Matrix(
            (round(x, precision) for x in row)
            for row in self.data
        )

    # @overload
    # def __getitem__(self, key: Tuple[slice, Literal[0, 1, 2]]) -> ThreeFloats:
    #     ...

    # @overload
    # def __getitem__(self, key: Tuple[Literal[0, 1, 2], slice]) -> ThreeFloats:
    #     ...

    # def __getitem__(self, key: Union[
    #     Tuple[slice, Literal[0, 1, 2]],
    #     Tuple[Literal[0, 1, 2], slice],
    # ]) -> Union[float, ThreeFloats]:
    #     a, b = key

    #     if isinstance(a, slice):
    #         return tuple(
    #             x[b] for x in self.data[a]
    #         )

    #     return self.data[a]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented

        return self.data == other.data

    def __hash__(self) -> int:
        return hash(self.data)

    def __repr__(self) -> str:
        return '{}((\n    {},\n))'.format(
            type(self).__name__,
            ',\n    '.join(repr(x) for x in self.data),
        )

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
    # TODO: shouldn't round eventually, though it makes development somewhat easier.
    )).round(1)


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
