#!/usr/bin/env python

from __future__ import annotations

import math
import unittest
from typing import Tuple

from . import vectors
from .matrix import Matrix
from .vectors import Vector

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
                    f"{a} should be the same direction as {b}",
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
                    f"{a} should not be the same direction as {b}",
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
                    f"Wrong unit vector for {vec}.",
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
                    f"Wrong cross product {vec_a} × {vec_b}.",
                )

                # Also check the other way around, which is defined as the reverse
                expected_rev = -expected
                cp_rev = vectors.cross_product(vec_b, vec_a)
                self.assertEqual(
                    expected_rev,
                    cp_rev,
                    f"Wrong cross product {vec_b} × {vec_a}.",
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
            (
                # Regression test for input which manages to be out of bounds
                # for cos theta due to floating point rounding errors.
                180,
                Vector((-0.1757748978918965, -0.027978574520328252, -0.09121614242503248)),
                Vector((0.8788744894594824, 0.13989287260164124, 0.4560807121251624)),
            ),
        )

        for case in cases:
            with self.subTest(case):
                expected, vec_a, vec_b = case
                actual = vectors.angle_between(vec_a, vec_b)
                self.assertEqual(
                    math.radians(expected),
                    actual,
                    "Wrong angle between vectors.",
                )


if __name__ == '__main__':
    unittest.main()
