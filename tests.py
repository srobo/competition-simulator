#!/usr/bin/env python

import unittest

from convert import Matrix


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


class TransformationTests(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
