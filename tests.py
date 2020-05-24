#!/usr/bin/env python

import math
import unittest
from typing import Tuple, Sequence

import vectors
from matrix import Matrix
from convert import WebotsOrientation, rotation_matrix_from_axis_and_angle
from vectors import Vector

SimpleVector = Tuple[float, float, float]


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
        I = Matrix((  # noqa:E741 # 'I' is not ambiguous in this context
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

    def test_identity_multiply_simple_vector(self) -> None:
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

    def test_identity_multiply_vector(self) -> None:
        A = Matrix((
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
        ))

        v = Vector((1, 2, 3))

        result = A * v

        self.assertEqual(v, result)

        result = v * A

        self.assertEqual(v, result)

    def test_multiply_vector(self) -> None:
        A = Matrix((
            (1, 2, 3),
            (4, 5, 6),
        ))

        v = Vector((1, 2, 3))
        expected = Vector((14, 32))

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

    def test_sub(self) -> None:
        A = Matrix((
            (5, 8, 8),
            (3, 5, 28),
        ))

        B = Matrix((
            (1, 2, 3),
            (4, 5, 6),
        ))

        C = A - B

        E = Matrix((
            (4, 6, 5),
            (-1, 0, 22),
        ))

        self.assertEqual(E, C)


class VectorTests(unittest.TestCase):
    def test_same_direction(self) -> None:
        cases = (
            (Vector((0.00001, 0, 1)), Vector((-0.00001, 0, 1))),
            (Vector((1, 0, 1)), Vector((1, 0, 1))),
            (Vector((1.1, 0, 1)), Vector((1, 0, 1.1))),
            (Vector((2, 0, 2)), Vector((1, 0, 1))),
        )

        for case in cases:
            with self.subTest(case):
                a, b = case
                self.assertTrue(
                    vectors.are_same_direction(a, b),
                    "{0} should be the same direction as {1}".format(a, b),
                )

    def test_not_same_direction(self) -> None:
        cases = (
            (Vector((1, 0, 1)), Vector((1, 1, 0))),
            (Vector((1, 0, 1)), Vector((0, 0, 1))),
            (Vector((1, 0, 1)), Vector((0, 0, 0))),
        )

        for case in cases:
            with self.subTest(case):
                a, b = case
                self.assertFalse(
                    vectors.are_same_direction(a, b),
                    "{0} should not be the same direction as {1}".format(a, b),
                )

    def test_unit_vector(self) -> None:
        cases = (
            (Vector((1, 0, 0)), Vector((1, 0, 0))),
            (Vector((2, 0, 0)), Vector((1, 0, 0))),
        )

        for case in cases:
            with self.subTest(case):
                vec, expected = case
                unit_vec = vectors.unit_vector(vec)
                self.assertEqual(
                    expected,
                    unit_vec,
                    "Wrong unit vector for {0}.".format(vec),
                )

    def test_vector_sum(self) -> None:
        cases = (
            (Vector((1, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 0))),
            (Vector((1, 1, 1)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))),
            (Vector((1, 1, 0)), Vector((1, 0, -1)), Vector((0, 1, 1))),
        )

        for case in cases:
            with self.subTest(case):
                expected, *vectors = case
                actual = sum(vectors, Vector((0, 0, 0)))
                self.assertEqual(expected, actual, "Wrong vector sum.")

    def test_cross_product(self) -> None:
        cases = (
            # Self
            (Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((1, 0, 0))),
            (Vector((0, 0, 0)), Vector((0, 1, 0)), Vector((0, 1, 0))),

            # Unit vectors
            (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))),
            (Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))),

            # Other vectors
            (Vector((4, 0, 0)), Vector((0, 2, 0)), Vector((0, 0, 2))),
        )

        for case in cases:
            with self.subTest(case):
                expected, vec_a, vec_b = case

                cp = vectors.cross_product(vec_a, vec_b)
                self.assertEqual(
                    expected,
                    cp,
                    "Wrong cross product {0} × {1}.".format(vec_a, vec_b),
                )

                # Also check the other way around, which is defined as the reverse
                expected_rev = -expected
                cp_rev = vectors.cross_product(vec_b, vec_a)
                self.assertEqual(
                    expected_rev,
                    cp_rev,
                    "Wrong cross product {0} × {1}.".format(vec_b, vec_a),
                )

    def test_dot_product_self(self) -> None:
        vec = Vector((1, 0, 0))
        dp = vectors.dot_product(vec, vec)
        self.assertEqual(1, dp, "Dot product of a vector and itself is 1")

    def test_dot_product_orthogonal(self) -> None:
        vec_a = Vector((1, 0, 0))
        vec_b = Vector((0, 1, 0))

        dp = vectors.dot_product(vec_a, vec_b)
        self.assertEqual(0, dp, "Dot product of two perpendicular unit vectors is 0")

        dp = vectors.dot_product(vec_b, vec_a)
        self.assertEqual(0, dp, "Dot product of two perpendicular unit vectors is 0")

    def test_angle_between(self) -> None:
        cases = (
            (0, Vector((1, 0, 0)), Vector((1, 0, 0))),
            (180, Vector((1, 0, 0)), Vector((-1, 0, 0))),
            (90, Vector((1, 0, 0)), Vector((0, 1, 0))),
            (90, Vector((2, 0, 0)), Vector((0, 0, 2))),
        )

        for case in cases:
            with self.subTest(case):
                expected, vec_a, vec_b = case
                actual = vectors.angle_between(vec_a, vec_b)
                self.assertEqual(expected, actual, "Wrong angle between vectors.")


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
        expected_vector: SimpleVector,
        input_orientation: WebotsOrientation,
    ) -> None:
        original = (1, 1, 1)

        R = rotation_matrix_from_axis_and_angle(input_orientation)

        R = round(R, 1)  # type: ignore[call-overload]

        result = R * original

        self.assertEqual(expected_vector, result)

    def assertPositions(
        self,
        vectors: Sequence[Tuple[str, SimpleVector, WebotsOrientation]],
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
