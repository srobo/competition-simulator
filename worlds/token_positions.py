from __future__ import annotations

import math
import textwrap
from typing import Literal

TokenType = Literal['B', 'S', 'G']

positions: list[tuple[TokenType, float, float]] = [
    ("B", 2.525, 1.100),  # Closest to starting area
    ("B", 1.000, 1.000),  # Closest to the arena centre
    ("B", 1.550, 1.550),  # Furthest from any walls
    ("B", 0.800, 2.225),  # Closest to the next starting area
    ("B", 1.100, 2.525),  # Next to the closest to the starting area
    ("S", 2.525, 2.525),  # In the corner
    ("S", 2.325, 1.815),  # Closer silver one to the starting area
    ("S", 1.815, 2.325),  # Further silver one to the starting area
    ("G", 0.160, 0.435),  # Gold one in the corner
]


def get_name(color: TokenType) -> str:
    if color == "B":
        return "SRToken_Bronze"
    if color == "S":
        return "SRToken_Silver"
    if color == "G":
        return "SRToken_Gold"
    raise ValueError("Invalid color")


def get_height(color: TokenType) -> float:
    if color == "B":
        return 0.061
    if color == "S":
        return 0.061
    if color == "G":
        return 0.136
    raise ValueError("Invalid color")


def rotate(x: float, y: float, angle: float) -> tuple[float, float]:
    """ Rotate given coordinate around the origin"""
    return (
        x * math.cos(angle) - y * math.sin(angle),
        x * math.sin(angle) + y * math.cos(angle),
    )


global_id = 0
for corner in range(4):
    angle = corner * (math.pi / 2)
    print(f"# ---  Corner {corner}  ---")  # noqa:T201
    for color, x, y in positions:
        token_name = get_name(color)
        height = get_height(color)
        x, y = rotate(x, y, angle)
        print(textwrap.dedent(  # noqa:T201
            f"""
              {token_name} {{
                translation {x:.3f} {y:.3f} {height:.3f}
                model "B{global_id}"
              }}
            """,
        ).strip())
        global_id += 1
