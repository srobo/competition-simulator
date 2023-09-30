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

from .types import Orientation


class WebotsOrientation(NamedTuple):
    x: float
    y: float
    z: float
    theta: float


def rotation_matrix_from_axis_and_angle(orientation: WebotsOrientation) -> Matrix:
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
    ))


def yaw_pitch_roll_from_axis_and_angle(orientation: WebotsOrientation) -> Orientation:
    x, y, z, theta = orientation

    sin_theta = math.sin(theta)
    one_minus_cos_theta = 1 - math.cos(theta)

    # https://www.euclideanspace.com/maths/geometry/rotations/conversions/angleToEuler/index.htm
    heading = math.atan2(
        y * sin_theta - x * z * one_minus_cos_theta,
        1 - (y ** 2 + z ** 2) * one_minus_cos_theta,
    )
    attitude = math.asin(x * y * one_minus_cos_theta + -z * sin_theta)
    bank = math.atan2(
        x * sin_theta - y * z * one_minus_cos_theta,
        1 - (x ** 2 + z ** 2) * one_minus_cos_theta,
    )

    return Orientation(
        yaw=attitude,
        roll=-bank,
        pitch=heading,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('x')
    parser.add_argument('y')
    parser.add_argument('z')
    parser.add_argument('theta')
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    webots_orientation = WebotsOrientation(
        args.x,
        args.y,
        args.z,
        args.theta,
    )
    print(rotation_matrix_from_axis_and_angle(webots_orientation))  # noqa: T201
    print(yaw_pitch_roll_from_axis_and_angle(webots_orientation))  # noqa: T201


if __name__ == '__main__':
    main(parse_args())
