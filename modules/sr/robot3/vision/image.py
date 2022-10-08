"""
Utilities for working with "objects" as they appear on a flat image.
"""

from __future__ import annotations

from typing import Tuple

# Units are pixels
Point = Tuple[int, int]
Size = Tuple[int, int]


class Rectangle:
    """
    A rectangular axis-aligned bounding-box.

    We use this primarily for its detection of whether or not it overlaps with
    another instance within the same plane.
    """

    def __init__(self, position: Point, size: Size) -> None:
        p_x, p_y = position
        s_x, s_y = size

        self.corners = (
            position,
            (p_x + s_x, p_y + s_y),
        )

    @property
    def x_min(self) -> int:
        (x_1, y_1), (x_2, y_2) = self.corners
        return min(x_1, x_2)

    @property
    def x_max(self) -> int:
        (x_1, y_1), (x_2, y_2) = self.corners
        return max(x_1, x_2)

    @property
    def y_min(self) -> int:
        (x_1, y_1), (x_2, y_2) = self.corners
        return min(y_1, y_2)

    @property
    def y_max(self) -> int:
        (x_1, y_1), (x_2, y_2) = self.corners
        return max(y_1, y_2)

    def overlaps(self, other: 'Rectangle') -> bool:
        # If one rectangle fully contains the other then we want the "outer" one
        # to be in `a`. this helps ensure that this is symetrical.
        a, b = (self, other) if self.x_min < other.x_min else (other, self)

        return (
            a.x_min <= b.x_min < a.x_max or
            a.x_min < b.x_max <= a.x_max
        ) and (
            a.y_min <= b.y_min < a.y_max or
            a.y_min < b.y_max <= a.y_max
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rectangle):
            return NotImplemented

        return self.corners == other.corners

    def __hash__(self) -> int:
        return hash(self.corners)

    def __repr__(self) -> str:
        (x_1, y_1), (x_2, y_2) = position, _ = self.corners
        size = (x_2 - x_1, y_2 - y_1)
        return f'Rectangle({position!r}, {size!r})'
