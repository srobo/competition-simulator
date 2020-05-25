#!/usr/bin/env python

import math
import unittest
from typing import Tuple, Sequence

import vectors
from image import Rectangle
from matrix import Matrix
from tokens import Token, FaceName, Orientation
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
    def test_multiply_float(self) -> None:
        v = Vector((1, 2, 3))

        expected = Vector((2.5, 5, 7.5))

        result = v * 2.5

        self.assertEqual(expected, result)

        result = 2.5 * v

        self.assertEqual(expected, result)

    def test_divide_float(self) -> None:
        v = Vector((12, 15, 3))

        expected = Vector((2, 2.5, 0.5))

        result = v / 6

        self.assertEqual(expected, result)

    def test_add(self) -> None:
        a = Vector((1, 2, 3))

        b = Vector((4, 6, 5))

        c = a + b

        expected = Vector((5, 8, 8))

        self.assertEqual(expected, c)

    def test_sub(self) -> None:
        a = Vector((5, 8, 8))

        b = Vector((1, 2, 3))

        c = a - b

        expected = Vector((4, 6, 5))

        self.assertEqual(expected, c)

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


class FaceTests(unittest.TestCase):
    def assertOrientation(
        self,
        expected_orientation: Orientation,
        webots_orientation: WebotsOrientation,
        face_name: FaceName,
    ) -> None:
        token = Token(
            # Position doesn't matter for this test.
            position=vectors.ZERO_3VECTOR,
        )

        token.rotate(rotation_matrix_from_axis_and_angle(webots_orientation))

        face = token.face(face_name)

        actual = face.orientation()
        actual = Orientation(*(round(x, 2) for x in actual))

        self.assertEqual(expected_orientation, actual, "Wrong orientation")

    def test_normals(self) -> None:
        cases = {
            FaceName.Top: Vector((0, 1, 0)),
            FaceName.Bottom: Vector((0, -1, 0)),
            FaceName.Left: Vector((-1, 0, 0)),
            FaceName.Right: Vector((1, 0, 0)),
            FaceName.Front: Vector((0, 0, -1)),
            FaceName.Rear: Vector((0, 0, 1)),
        }

        token = Token(
            # Position doesn't matter for these tests.
            position=vectors.ZERO_3VECTOR,
        )

        for face_name, expected_direction in cases.items():
            with self.subTest(face_name):
                face = token.face(face_name)
                actual = face.normal()

                self.assertEqual(expected_direction, actual, "Wrong normal unit vector")

    def test_centre_global(self) -> None:
        token = Token(
            position=Vector((6, 0, 10)),
            size=2,
        )

        front_face = token.face(FaceName.Front)

        # Token centre 6 to the right (X) and 10 back (Z)
        # Centre of the front face is 2 towards us (Z) from that
        # Centre of the front face is therefore 6 to the right (X) and 8 back (Z)

        self.assertEqual(
            Vector((6, 0, 8)),
            front_face.centre_global(),
        )

        # By pythagoras, the center of the front face is therefore 10 away overall

        self.assertEqual(10, front_face.distance())

    def test_top_midpoint(self) -> None:
        cases = {
            # Back, away from the observer is defined as the "top"
            FaceName.Top: Vector((0, 1, 1)),
            FaceName.Bottom: Vector((0, -1, 1)),
            # Top
            FaceName.Left: Vector((-1, 1, 0)),
            FaceName.Right: Vector((1, 1, 0)),
            FaceName.Front: Vector((0, 1, -1)),
            FaceName.Rear: Vector((0, 1, 1)),
        }

        token = Token(
            # Position doesn't matter for these tests.
            position=vectors.ZERO_3VECTOR,
        )

        for face_name, expected_direction in cases.items():
            with self.subTest(face_name):
                face = token.face(face_name)
                actual = face.top_midpoint()

                self.assertEqual(expected_direction, actual, "Wrong top edge midpoint")

    def test_front_face_orientation_rot_x(self) -> None:
        cases = (
            # Token has been leaned 45° backwards, about X
            (WebotsOrientation(-1, 0, 0, math.pi / 4), 45),
            # Token has been leaned 45° forwards, about X
            (WebotsOrientation(1, 0, 0, math.pi / 4), -45),

            # Based on data from Webots
            # Token 90° backwards, about X
            (WebotsOrientation(-1, 0, 0, math.pi / 2), 90),
            (WebotsOrientation(-0.999999999999942, -2.849321921363655e-07, -1.870076020351921e-07, 1.5529951171463792), 88.98),  # noqa:E501
            # Token 90° forwards, about X
            (WebotsOrientation(1, 0, 0, math.pi / 2), -90),
            (WebotsOrientation(0.9999999999999977, -3.3035051017161785e-08, -6.047316465407898e-08, 1.587925455878411), -89.02),  # noqa:E501
        )

        for webots_orientation, expected_degrees in cases:
            with self.subTest(expected_degrees):
                self.assertOrientation(
                    Orientation(expected_degrees, 0, 0),
                    webots_orientation,
                    FaceName.Front,
                )

    def test_front_face_orientation_rot_y(self) -> None:
        cases = (
            # Straight on.
            (WebotsOrientation(0, 1, 0, 0), 0),
            # Half way to position B (see TransformationTests).
            # Token has been turned 45° to the left (clockwise from above) about Y.
            (WebotsOrientation(0, -1, 0, math.pi / 4), 45),
            # Half way to position C (see TransformationTests).
            # Token has been turned 45° to the right (anticlockwise from above) about Y.
            (WebotsOrientation(0, 1, 0, math.pi / 4), -45),
            # A third of the way to position C (see TransformationTests).
            # Token has been turned 30° to the right (anticlockwise from above) about Y.
            (WebotsOrientation(0, 1, 0, math.pi / 6), -30),
        )

        for webots_orientation, expected_degrees in cases:
            with self.subTest(expected_degrees):
                self.assertOrientation(
                    Orientation(0, expected_degrees, 0),
                    webots_orientation,
                    FaceName.Front,
                )

    def test_front_face_orientation_rot_z(self) -> None:
        cases = (
            # Half way to position A, row 2 (see TransformationTests).
            # Token has been turned 45° to the right (clockwise) about Z.
            (WebotsOrientation(0, 0, -1, math.pi / 4), -45),
            # Token has been turned 45° to the left (anticlockwise) about Z.
            (WebotsOrientation(0, 0, 1, math.pi / 4), 45),
            # Token has been upside down about Z.
            (WebotsOrientation(0, 0, 1, math.pi), 180),
        )

        for webots_orientation, expected_degrees in cases:
            with self.subTest(expected_degrees):
                self.assertOrientation(
                    Orientation(0, 0, expected_degrees),
                    webots_orientation,
                    FaceName.Front,
                )

    def test_combined_rotations(self) -> None:
        # Cases B & C from the second row of angles.png. We ignore case D
        # because in that scenario the marker is behind the token an cannot be
        # seen. libkoki somewhat deliberately leaves this case undefined, so we
        # do the same.
        # The second row of data are based on first rotating the token 90°
        # clockwise (from the perspective of the camera) on its side.

        one_over_root_three = 3 ** -0.5

        cases = (
            (
                'B',
                Orientation(0, 90, -90),
                WebotsOrientation(
                    -one_over_root_three,
                    -one_over_root_three,
                    -one_over_root_three,
                    math.pi * 2 / 3,  # ~2.114
                ),
            ),
            (
                'C',
                Orientation(0, -90, -90),
                WebotsOrientation(
                    one_over_root_three,
                    one_over_root_three,
                    -one_over_root_three,
                    math.pi * 2 / 3,  # ~2.075
                ),
            ),
        )

        for name, expected_orientation, webots_orientation in cases:
            with self.subTest(name):
                self.assertOrientation(
                    expected_orientation,
                    webots_orientation,
                    FaceName.Front,
                )


class TokenTests(unittest.TestCase):
    def test_faces_visible_to_origin(self) -> None:
        # The first row of data in angles.png, which are equivalent to 90°
        # rotations about the y axis.
        cases = (
            (
                'A',
                FaceName.Front,
                WebotsOrientation(1, 0, 0, 0),
            ),
            (
                'B',
                FaceName.Right,
                WebotsOrientation(0, -1, 0, math.pi / 2),
            ),
            (
                'C',
                FaceName.Left,
                WebotsOrientation(0, 1, 0, math.pi / 2),
            ),
            (
                'D',
                FaceName.Rear,
                WebotsOrientation(0, 1, 0, math.pi),
            ),
        )

        for name, expected_face, webots_orientation in cases:
            with self.subTest(name):
                # position is somewhat irrelevant, just needs to be believable
                token = Token(position=Vector((0, 0, 4)))
                token.rotate(rotation_matrix_from_axis_and_angle(webots_orientation))

                self.assertEqual(
                    [expected_face],
                    [x.name for x in token.visible_faces()],
                )


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


class RectangleTests(unittest.TestCase):
    def test_no_overlap(self) -> None:
        a = Rectangle((0, 0), (1, 1))
        b = Rectangle((2, 2), (1, 1))

        self.assertFalse(a.overlaps(b), "{} should not overlap {}".format(a, b))
        self.assertFalse(b.overlaps(a), "{} should not overlap {}".format(b, a))

    def test_no_overlap_when_touching(self) -> None:
        a = Rectangle((0, 0), (1, 1))
        b = Rectangle((1, 1), (1, 1))

        self.assertFalse(a.overlaps(b), "{} should not overlap {}".format(a, b))
        self.assertFalse(b.overlaps(a), "{} should not overlap {}".format(b, a))

    def test_has_overlap_self(self) -> None:
        a = Rectangle((1, 1), (2, 2))

        self.assertTrue(a.overlaps(a), "{} should overlap {}".format(a, a))

    def test_has_partial_overlap(self) -> None:
        a = Rectangle((1, 1), (2, 2))
        b = Rectangle((2, 2), (2, 2))

        self.assertTrue(a.overlaps(b), "{} should overlap {}".format(a, b))
        self.assertTrue(b.overlaps(a), "{} should overlap {}".format(b, a))

    def test_has_overlap_contained(self) -> None:
        a = Rectangle((1, 1), (5, 5))
        b = Rectangle((2, 2), (2, 2))

        self.assertTrue(a.overlaps(b), "{} should overlap {}".format(a, b))
        self.assertTrue(b.overlaps(a), "{} should overlap {}".format(b, a))


if __name__ == '__main__':
    unittest.main()
