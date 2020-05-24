#!/usr/bin/env python

import math
import unittest
from typing import Tuple, Sequence

from convert import (
    Matrix,
    WebotsOrientation,
    rotation_matrix_from_axis_and_angle,
)

Vector = Tuple[float, float, float]


class MatrixTests(unittest.TestCase):
    def test_transpose(self) -> None:
        A = Matrix((
            (1, 2, 3),
            (2, 3, 4),
            (6, 7, 8),
        ))

        B = A.transpose()

        E = Matrix((
            (1, 2, 6),
            (2, 3, 7),
            (3, 4, 8),
        ))

        self.assertEqual(E, B)

    def test_multiply_identity(self) -> None:
        I = Matrix((
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
        ))
        A = Matrix((
            (1, 2, 3),
            (2, 3, 4),
            (6, 7, 8),
        ))

        B = I @ A

        self.assertEqual(A, B)

    def test_multiply(self) -> None:
        A = Matrix((
            (1, 2, 3),
            (1, 0, 1),
            (2, 2, 2),
        ))
        B = Matrix((
            (1, 0, 1),
            (0, 5, 0),
            (3, 0, 10),
        ))

        C = A @ B

        E = Matrix((
            (10, 10, 31),
            (4, 0, 11),
            (8, 10, 22),
        ))

        self.assertEqual(E, C)

    def test_multiply_reversed(self) -> None:
        B = Matrix((
            (1, 0, 1),
            (0, 5, 0),
            (3, 0, 10),
        ))
        A = Matrix((
            (1, 2, 3),
            (1, 0, 1),
            (2, 2, 2),
        ))

        C = B @ A

        E = Matrix((
            (3, 4, 5),
            (5, 0, 5),
            (23, 26, 29),
        ))

        self.assertEqual(E, C)

    def test_identity_multiply_vector(self) -> None:
        A = Matrix((
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
        ))

        v = (1, 2, 3)

        result = A * v

        self.assertEqual(v, result)

        result = v * A

        self.assertEqual(v, result)

    def test_multiply_vector(self) -> None:
        A = Matrix((
            (1, 2, 3),
            (4, 5, 6),
        ))

        v = (1, 2, 3)
        expected = (14, 32)

        result = A * v

        self.assertEqual(expected, result)

        result = v * A

        self.assertEqual(expected, result)

    def test_add(self) -> None:
        A = Matrix((
            (1, 2, 3),
            (4, 5, 6),
        ))

        B = Matrix((
            (4, 6, 5),
            (-1, 0, 22),
        ))

        C = A + B

        E = Matrix((
            (5, 8, 8),
            (3, 5, 28),
        ))

        self.assertEqual(E, C)


class TransformationTests(unittest.TestCase):
    # All tests operate by validating the relative position of what is initially
    # the top-right-back corner (with co-ordinates (1, 1, 1)) on the token after
    # some movement of the token, the observer or both.
    #
    # Positions:
    #  - A is with the observer in front of the token
    #
    #  - B is with the observer to the right of the token, equivalent to an
    #    additional rotation of the token 90° clockwise from above about y
    #
    #  - C is with the observer to the left of the token, equivalent to an
    #    additional rotation of the token 90° anticlockwise from above about y
    #
    #  - D is with the observer behind the token, equivalent to an
    #    additional rotation of the token 180° about y

    def assertPosition(
        self,
        expected_vector: Vector,
        input_orientation: WebotsOrientation,
    ) -> None:
        original = (1, 1, 1)

        R = rotation_matrix_from_axis_and_angle(input_orientation)

        R = R.round(1)  # type: ignore[call-overload]

        result = R * original

        self.assertEqual(expected_vector, result)

    def assertPositions(
        self,
        vectors: Sequence[Tuple[str, Vector, WebotsOrientation]],
    ) -> None:
        for position, expected_vector, input_orientation in vectors:
            with self.subTest(position):
                self.assertPosition(expected_vector, input_orientation)

    def test_initial_token_position(self) -> None:
        # The first row of data in angles.png, which are equivalent to 90°
        # rotations about the y axis.

        self.assertPositions([
            (
                'A',
                (1, 1, 1),
                WebotsOrientation(1, 0, 0, 0),
            ),
            (
                'B',
                (1, 1, -1),
                WebotsOrientation(0, -1, 0, math.pi / 2),
            ),
            (
                'C',
                (-1, 1, 1),
                WebotsOrientation(0, 1, 0, math.pi / 2),
            ),
            (
                'D',
                (-1, 1, -1),
                WebotsOrientation(0, 1, 0, math.pi),
            ),
        ])

    def test_token_on_side_90_degrees_clockwise_from_observer_perspective(self) -> None:
        # The second row of data in angles.png, which are based on first
        # rotating the token 90° clockwise (from the perspective of the camera)
        # on its side.

        one_over_root_two = 2 ** -0.5
        one_over_root_three = 3 ** -0.5

        self.assertPositions([
            (
                'A',
                (1, -1, 1),
                WebotsOrientation(0, 0, -1, math.pi / 2),
            ),
            (
                'B',
                (1, -1, -1),
                WebotsOrientation(
                    -one_over_root_three,
                    -one_over_root_three,
                    -one_over_root_three,
                    2.114,
                ),
            ),
            (
                'C',
                (-1, -1, 1),
                WebotsOrientation(
                    one_over_root_three,
                    one_over_root_three,
                    -one_over_root_three,
                    2.075,
                ),
            ),
            (
                'D',
                (-1, -1, -1),
                WebotsOrientation(
                    one_over_root_two,
                    one_over_root_two,
                    0,
                    3.118,
                ),
            ),
        ])

    def test_token_upside_down_180_degrees_clockwise_from_observer_perspective(self) -> None:
        # The third row of data in angles.png, which are based on first rotating
        # the token 180° clockwise (from the perspective of the camera) so it is
        # upside down, but the face which was initially facing the observer is
        # still (initially) facing the observer.

        one_over_root_two = 2 ** -0.5

        self.assertPositions([
            (
                'A',
                (-1, -1, 1),
                WebotsOrientation(0, 0, -1, math.pi),
            ),
            (
                'B',
                (1, -1, 1),
                WebotsOrientation(
                    one_over_root_two,
                    0,
                    one_over_root_two,
                    3.12,
                ),
            ),
            (
                'C',
                (-1, -1, -1),
                WebotsOrientation(
                    one_over_root_two,
                    0,
                    -one_over_root_two,
                    3.12,
                ),
            ),
            (
                'D',
                (1, -1, -1),
                WebotsOrientation(1, 0, 0, 3.112),
            ),
        ])

    def test_token_upside_down_270_degrees_clockwise_from_observer_perspective(self) -> None:
        # The third row of data in angles.png, which are based on first rotating
        # the token 270° clockwise (from the perspective of the camera) so it is
        # upside down, but the face which was initially facing the observer is
        # still (initially) facing the observer.

        one_over_root_two = 2 ** -0.5
        one_over_root_three = 3 ** -0.5

        self.assertPositions([
            (
                'A',
                (-1, 1, 1),
                WebotsOrientation(0, 0, 1, math.pi / 2),
            ),
            (
                'B',
                (1, 1, 1),
                WebotsOrientation(
                    one_over_root_three,
                    -one_over_root_three,
                    one_over_root_three,
                    2.08,
                ),
            ),
            (
                'C',
                (-1, 1, -1),
                WebotsOrientation(
                    -one_over_root_three,
                    one_over_root_three,
                    one_over_root_three,
                    2.11,
                ),
            ),
            (
                'D',
                (1, 1, -1),
                WebotsOrientation(
                    one_over_root_two,
                    -one_over_root_two,
                    0,
                    3.12,
                ),
            ),
        ])


if __name__ == '__main__':
    unittest.main()
