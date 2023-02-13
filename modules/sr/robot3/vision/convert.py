#!/usr/bin/env python

"""
Convert from Webots' (x, y, z, θ) axis-angle orientation to a slightly more
competitor-friendly format.
"""

from __future__ import annotations

import math
import argparse
from typing import NamedTuple

from sr.robot3.coordinates.matrix import Matrix


class WebotsOrientation(NamedTuple):
    x: float
    y: float
    z: float
    theta: float


def rotation_matrix_from_axis_and_angle(orientation: WebotsOrientation) -> Matrix:
    # Webots' axes are different to ours. Account for that in the unpacking
    z, x, y, theta = orientation

    # Seemingly webots' X is upside down versus Zoloto's. Note: this also
    # changes the handedness of the axes.
    x *= -1

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
    print(rotation_matrix_from_axis_and_angle(WebotsOrientation(  # noqa: T201
        args.x,
        args.y,
        args.z,
        args.theta,
    )))


if __name__ == '__main__':
    main(parse_args())
