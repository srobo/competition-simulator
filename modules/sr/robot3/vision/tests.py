#!/usr/bin/env python

from __future__ import annotations

import unittest
from typing import Tuple

from sr.robot3.coordinates import vectors
from sr.robot3.vision.image import Rectangle
from sr.robot3.vision.markers import FiducialMarker
from sr.robot3.coordinates.vectors import Vector

SimpleVector = Tuple[float, float, float]


class FaceTests(unittest.TestCase):
    def test_normals(self) -> None:
        marker = FiducialMarker(
            # Position doesn't matter for these tests.
            position=vectors.ZERO_3VECTOR,
        )

        actual = marker.normal()
        self.assertEqual(
            Vector((-1, 0, 0)),
            actual,
            "Wrong normal unit vector",
        )

    def test_top_midpoint(self) -> None:
        marker = FiducialMarker(
            # Position doesn't matter for these tests.
            position=vectors.ZERO_3VECTOR,
        )

        actual = marker.top_midpoint()

        self.assertEqual(
            Vector((0.0001, 1, 0)),
            actual,
            "Wrong top edge midpoint",
        )


class RectangleTests(unittest.TestCase):
    def test_no_overlap(self) -> None:
        a = Rectangle((0, 0), (1, 1))
        b = Rectangle((2, 2), (1, 1))

        self.assertFalse(a.overlaps(b), f"{a} should not overlap {b}")
        self.assertFalse(b.overlaps(a), f"{b} should not overlap {a}")

    def test_no_overlap_when_touching(self) -> None:
        a = Rectangle((0, 0), (1, 1))
        b = Rectangle((1, 1), (1, 1))

        self.assertFalse(a.overlaps(b), f"{a} should not overlap {b}")
        self.assertFalse(b.overlaps(a), f"{b} should not overlap {a}")

    def test_has_overlap_self(self) -> None:
        a = Rectangle((1, 1), (2, 2))

        self.assertTrue(a.overlaps(a), f"{a} should overlap {a}")

    def test_has_partial_overlap(self) -> None:
        a = Rectangle((1, 1), (2, 2))
        b = Rectangle((2, 2), (2, 2))

        self.assertTrue(a.overlaps(b), f"{a} should overlap {b}")
        self.assertTrue(b.overlaps(a), f"{b} should overlap {a}")

    def test_has_overlap_contained(self) -> None:
        a = Rectangle((1, 1), (5, 5))
        b = Rectangle((2, 2), (2, 2))

        self.assertTrue(a.overlaps(b), f"{a} should overlap {b}")
        self.assertTrue(b.overlaps(a), f"{b} should overlap {a}")


if __name__ == '__main__':
    unittest.main()
