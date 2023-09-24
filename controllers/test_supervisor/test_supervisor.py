from __future__ import annotations

import os
import sys
import math
import unittest
import threading
from pathlib import Path

# Webots specific library
from controller import Robot as WebotsRobot, Camera as WebotCamera, Supervisor

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

from sr.robot3.coordinates import Position  # isort:skip
from sr.robot3.vision import Orientation  # isort:skip
from sr.robot3.camera import Camera, Marker  # isort:skip
from sr.robot3.utils import get_robot_device  # isort:skip

ROBOT: WebotsRobot
TIMESTEP: int


class ApproximateFloat(float):
    def __neg__(self) -> ApproximateFloat:
        return ApproximateFloat(super().__neg__())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, float):
            return NotImplemented
        diff = abs(self - other)
        return round(diff, 5) == 0


def ApproximateOrientation(yaw: float, pitch: float, roll: float) -> Orientation:
    return Orientation(
        ApproximateFloat(yaw),
        ApproximateFloat(pitch),
        ApproximateFloat(roll),
    )


def ApproximatePosition(
    distance: int,
    horizontal_angle: float,
    vertical_angle: float,
) -> Position:
    return Position(
        distance=distance,
        horizontal_angle=ApproximateFloat(horizontal_angle),
        vertical_angle=ApproximateFloat(vertical_angle),
    )


class TestCamera(unittest.TestCase):
    maxDiff = None

    webot: WebotsRobot

    def get_camera(self, name: str) -> Camera:
        camera = Camera(
            self.webot,
            get_robot_device(self.webot, name, WebotCamera),
            self.lock,
        )
        # Warm up the camera
        with self.lock:
            self.webot.step(TIMESTEP)
            self.webot.step(TIMESTEP)
        return camera

    @classmethod
    def setUpClass(cls) -> None:
        cls.webot = ROBOT

    def setUp(self) -> None:
        self.lock = threading.Lock()

    def test_full(self) -> None:
        camera = self.get_camera('camera-marker-straight-ahead')

        markers = camera.see()

        self.assertEqual(
            [
                Marker(
                    id=2,
                    size=200,
                    position=Position(
                        distance=1000,
                        horizontal_angle=ApproximateFloat(0),
                        vertical_angle=ApproximateFloat(0),
                    ),
                    orientation=Orientation(0, ApproximateFloat(0), 0),
                ),
            ],
            markers,
        )

    def test_positions(self) -> None:
        REFERENCE_DISTANCE = 1000
        OFFSET = 200
        ANGLED_DISTANCE = int(math.sqrt(REFERENCE_DISTANCE ** 2 + OFFSET ** 2))
        ANGLE = ApproximateFloat(math.atan2(OFFSET, REFERENCE_DISTANCE))
        ZERO = ApproximateFloat(0)

        POSITIONS = [
            (
                'camera-marker-straight-ahead',
                Position(
                    distance=REFERENCE_DISTANCE,
                    horizontal_angle=ZERO,
                    vertical_angle=ZERO,
                ),
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/position/pos_left.png
                'camera-marker-slightly-left',
                Position(
                    distance=ANGLED_DISTANCE,
                    horizontal_angle=-ANGLE,
                    vertical_angle=ZERO,
                ),
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/position/pos_right.png
                'camera-marker-slightly-right',
                Position(
                    distance=ANGLED_DISTANCE,
                    horizontal_angle=ANGLE,
                    vertical_angle=ZERO,
                ),
            ),
            (
                'camera-marker-slightly-closer',
                Position(
                    distance=REFERENCE_DISTANCE - OFFSET,
                    horizontal_angle=ZERO,
                    vertical_angle=ZERO,
                ),
            ),
            (
                'camera-marker-slightly-further',
                Position(
                    distance=REFERENCE_DISTANCE + OFFSET,
                    horizontal_angle=ZERO,
                    vertical_angle=ZERO,
                ),
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/position/pos_up.png
                'camera-marker-slightly-up',
                Position(
                    distance=ANGLED_DISTANCE,
                    horizontal_angle=ZERO,
                    vertical_angle=ANGLE,
                ),
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/position/pos_down.png
                'camera-marker-slightly-down',
                Position(
                    distance=ANGLED_DISTANCE,
                    horizontal_angle=ZERO,
                    vertical_angle=-ANGLE,
                ),
            ),
        ]

        for name, position in POSITIONS:
            with self.subTest(name):
                camera = self.get_camera(name)
                marker, = camera.see()
                self.assertEqual(
                    position,
                    marker.position,
                    "Wrong position",
                )
                self.assertEqual(
                    ApproximateOrientation(0, 0, 0),
                    marker.orientation,
                    "Wrong orientation",
                )

    def test_orientations(self) -> None:
        QUARTER_PI = ApproximateFloat(math.pi / 4)

        ORIENTATIONS = [
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/yaw-45.png
                'camera-marker-turned-right',
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=0,
                    roll=0,
                ),
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/yaw45.png
                'camera-marker-turned-left',
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=0,
                    roll=0,
                ),
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/pitch45.png
                'camera-marker-leaning-back',
                Orientation(
                    yaw=0,
                    pitch=QUARTER_PI,
                    roll=0,
                ),
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/pitch-45.png
                'camera-marker-leaning-forwards',
                Orientation(
                    yaw=0,
                    pitch=-QUARTER_PI,
                    roll=0,
                ),
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/roll45.png
                'camera-marker-leaning-left',
                Orientation(
                    yaw=0,
                    pitch=0,
                    roll=QUARTER_PI,
                ),
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/roll-45.png
                'camera-marker-leaning-right',
                Orientation(
                    yaw=0,
                    pitch=0,
                    roll=-QUARTER_PI,
                ),
            ),
        ]

        for name, orientation in ORIENTATIONS:
            with self.subTest(name):
                camera = self.get_camera(name)
                marker, = camera.see()
                self.assertEqual(
                    orientation,
                    marker.orientation,
                    "Wrong orientation",
                )
                self.assertEqual(
                    ApproximatePosition(1000, 0, 0),
                    marker.position,
                    "Wrong position",
                )


def main() -> None:
    global ROBOT, TIMESTEP
    ROBOT = supervisor = Supervisor()
    TIMESTEP = int(supervisor.getBasicTimeStep())

    supervisor.step(TIMESTEP)

    tests = unittest.main(exit=False, buffer=True)

    # Ensure our printed output actually makes it to the console
    supervisor.step(TIMESTEP)
    supervisor.step(TIMESTEP)

    if os.environ.get('EXIT_AFTER_TESTS'):
        supervisor.simulationQuit(status=(
            0
            if tests.result.wasSuccessful()
            else 1
        ))


if __name__ == '__main__':
    main()
