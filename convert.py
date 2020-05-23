"""
Convert from Webots' (x, y, z, θ) axis-angle orientation to a slightly more
competitor-friendly format.
"""

import math
from typing import Tuple, Union, overload, NamedTuple

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


class RotationMatrix:
    @classmethod
    def from_axis_and_angle(cls, orientation: WebotsOrientation) -> 'RotationMatrix':
        x, y, z, theta = orientation

        if round(x ** 2 + y ** 2 + z ** 2, 5) != 1:
            raise ValueError("Orientation vector is not a unit vector")

        cos_theta = math.cos(theta)
        one_minus_cos_theta = 1 - cos_theta
        sin_theta = math.sin(theta)

        x_sin_theta = x * sin_theta
        y_sin_theta = y * sin_theta
        z_sin_theta = z * sin_theta

        x_y_one_minus_cos_theta = x * y * one_minus_cos_theta
        x_z_one_minus_cos_theta = x * z * one_minus_cos_theta

        return RotationMatrix((
            (
                cos_theta + x ** 2 * one_minus_cos_theta,
                x_y_one_minus_cos_theta - z_sin_theta,
                x_z_one_minus_cos_theta - y_sin_theta,
            ),
            (
                x_y_one_minus_cos_theta + z_sin_theta,
                cos_theta + y ** 2 * one_minus_cos_theta,
                x_y_one_minus_cos_theta - x_sin_theta,
            ),
            (
                x_z_one_minus_cos_theta - y_sin_theta,
                x_y_one_minus_cos_theta + x_sin_theta,
                cos_theta + z ** 2 * one_minus_cos_theta,
            ),
        ))

    def __init__(self, data: Tuple[ThreeFloats, ThreeFloats, ThreeFloats]) -> None:
        if len(data) != 3 or any(len(x) != 3 for x in data):
            raise ValueError("Malformed input to RotationMatrix: {!r}".format(data))

        self.data = tuple(tuple(round(y, 1) for y in x) for x in data)

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
        if not isinstance(other, RotationMatrix):
            return NotImplemented

        return self.data == other.data

    def __hash__(self) -> int:
        return hash(self.data)

    def __repr__(self) -> str:
        return '{}((\n    {},\n))'.format(
            type(self).__name__,
            ',\n    '.join(repr(x) for x in self.data),
        )
