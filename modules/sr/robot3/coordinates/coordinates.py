from __future__ import annotations

from typing import NamedTuple

from .polar import PolarCoord, polar_from_cartesian
from .vectors import Vector


class Cartesian(NamedTuple):
    x: float
    y: float
    z: float


class Point(NamedTuple):
    world: Cartesian
    polar: PolarCoord

    @classmethod
    def from_vector(cls, vector: Vector) -> Point:
        return cls(
            world=Cartesian(*vector.data),
            polar=polar_from_cartesian(vector),
        )
