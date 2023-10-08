#!/usr/bin/env python3

from __future__ import annotations

import math
import pathlib
import argparse
import textwrap
import itertools
import dataclasses
from typing import Iterator, NamedTuple

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


class BuiltPoses(NamedTuple):
    test_code: list[str]
    world_cameras: list[str]
    world_markers: list[str]


@dataclasses.dataclass(frozen=True)
class Value:
    python_symbol: str
    multiple: float

    @property
    def webots_value(self) -> float:
        return math.pi * self.multiple

    def name(self, axis: str) -> str | None:
        if not self.multiple:
            return None
        direction = 'pos' if self.multiple > 0 else 'neg'
        return f'{direction}-{axis}'


@dataclasses.dataclass(frozen=True)
class ZeroValue(Value):
    python_symbol: str = dataclasses.field(default='0', init=False)
    multiple: float = dataclasses.field(default=0, init=False)
    webots_value: float = dataclasses.field(default=0, init=False)


DISTANCE_OFFSET = 2

AXES = ('yaw', 'pitch', 'roll')
VALUES = (
    ZeroValue(),
    Value('QUARTER_PI', multiple=1 / 4),
    Value('-QUARTER_PI', multiple=-1 / 4),
)


TEST_DATA_TEMPLATE = '''
(
    '{camera_name}',
    Orientation(
        yaw={yaw.python_symbol},
        pitch={pitch.python_symbol},
        roll={roll.python_symbol},
    ),
    {marker_id},
),
'''

WORLD_CAMERA_TEMPLATE = '''
SRCamera {{
  name "{camera_name}"
  translation 0 {offset} 0
}}
'''

WORLD_MARKER_TEMPLATE = '''
Pose {{
  translation 1 {offset} 1
  rotation -1 0 0 {roll.webots_value}  # roll
  children [
    Pose {{
      rotation 0 1 0 {pitch.webots_value}  # pitch
      children [
        WallMarker {{
          rotation 0 0 -1 {yaw.webots_value}  # yaw
          name "{marker_name}"
          model "F{marker_id}"
          texture_url [
            "../textures/arena-markers/{marker_id}.png"
          ]
        }}
      ]
    }}
  ]
}}
'''


def values_with_at_most_one_zero() -> Iterator[tuple[Value, Value, Value]]:
    for values in itertools.product(VALUES, repeat=3):
        num_zeroes = sum(1 for x in values if not x.multiple)
        if num_zeroes > 1:
            continue

        yield values  # type: ignore[misc]


# Updating these file-content-insertion utils?
# Consider also updating `worlds/insert-tokens.py`


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


def build_poses() -> BuiltPoses:
    test_code = []
    world_cameras = []
    world_markers = []

    for marker_id, values in enumerate(values_with_at_most_one_zero()):
        offset = marker_id + 2
        identity = list(zip(AXES, values))
        name_parts = [y.name(x) for x, y in identity]
        name = '-'.join(x for x in name_parts if x)
        camera_name = f'camera-marker-{name}'

        test_code.append(TEST_DATA_TEMPLATE.format(
            camera_name=camera_name,
            marker_id=marker_id,
            **dict(identity),
        ))

        world_cameras.append(WORLD_CAMERA_TEMPLATE.format(
            camera_name=camera_name,
            offset=offset,
            **dict(identity),
        ))

        world_markers.append(WORLD_MARKER_TEMPLATE.format(
            marker_name=f'marker-{name}',
            offset=offset,
            marker_id=marker_id,
            **dict(identity),
        ))

    return BuiltPoses(
        test_code=test_code,
        world_cameras=world_cameras,
        world_markers=world_markers,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Template all non-trivial marker poses into our tests",
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

    poses = build_poses()

    output(
        "Tests",
        poses.test_code,
        REPO_ROOT / 'controllers' / 'test_supervisor' / 'test_supervisor.py',
        'ORIENTATIONS',
    )

    output(
        "Cameras",
        poses.world_cameras,
        REPO_ROOT / 'worlds' / 'Tests.wbt',
        'CAMERAS',
    )

    output(
        "Markers",
        poses.world_markers,
        REPO_ROOT / 'worlds' / 'Tests.wbt',
        'MARKERS',
    )


if __name__ == '__main__':
    main(parse_args())
