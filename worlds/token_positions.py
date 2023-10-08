#!/usr/bin/env python3

from __future__ import annotations

import math
import pathlib
import argparse
import textwrap
from typing import Literal

TokenType = Literal['B', 'S', 'G']

WORLDS_DIR = pathlib.Path(__file__).parent

POSITIONS: list[tuple[TokenType, float, float]] = [
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


# Updating these file-content-insertion utils?
# Consider also updating `script/testing/insert-poses.py`


def indented(parts: list[str], *, prefix: str) -> str:
    text = '\n'.join(x.strip() for x in parts)
    return textwrap.indent(text, prefix)


def find_line(lines: list[str], text: str, *, context: object) -> int:
    for idx, line in enumerate(lines):
        if line.strip() == text:
            return idx
    raise ValueError(f"{text!r} not found in {context}")


def insert(target: pathlib.Path, keyword: str, parts: list[str]) -> None:
    lines = target.read_text().splitlines(keepends=True)

    start = find_line(lines, f'# START_GENERATED:{keyword}', context=target)
    end = find_line(lines, f'# END_GENERATED:{keyword}', context=target)

    indent = ' ' * lines[start].find('#')
    content = indented(parts, prefix=indent)
    lines[start + 1:end] = [content + '\n']

    target.write_text(''.join(lines))


TOKEN_TEMPLATE = '''
{token_name} {{
  translation {x:.3f} {y:.3f} {height:.3f}
  model "{model_name}"
}}
'''


def build_output() -> list[str]:
    lines = []

    global_id = 0
    for corner in range(4):
        angle = corner * (math.pi / 2)
        lines.append(f"# ---  Corner {corner}  ---")

        for color, x, y in POSITIONS:
            token_name = get_name(color)
            height = get_height(color)
            x, y = rotate(x, y, angle)
            lines.append(TOKEN_TEMPLATE.format(
                token_name=token_name,
                x=x,
                y=y,
                height=height,
                model_name=f'B{global_id}',
            ))
            global_id += 1

    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Template tokens into the arena",
    )
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    def output(title: str, parts: list[str], target: pathlib.Path, keyword: str) -> None:
        if args.dry_run:
            print(f" -- {title} -- ")  # noqa: T201
            print(indented(parts, prefix='  '))  # noqa: T201
        else:
            insert(target, keyword, parts)

    lines = build_output()

    output(
        "Tokens",
        lines,
        WORLDS_DIR / 'Arena.wbt',
        'TOKENS',
    )


if __name__ == '__main__':
    main(parse_args())
