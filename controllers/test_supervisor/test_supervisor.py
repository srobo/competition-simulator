from __future__ import annotations

import os
import sys
import math
import unittest
import threading
import dataclasses
from pathlib import Path

# Webots specific library
from controller import (
    Robot as WebotsRobot,
    Camera as WebotCamera,
    Supervisor,
    CameraRecognitionObject as WebotsRecognitionObject,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

from sr.robot3.coordinates import Position, Vector  # isort:skip
from sr.robot3.vision import Orientation, markers_from_objects  # isort:skip
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


def Normal(x: float, y: float, z: float) -> Vector:
    return Vector((x, y, z))


def TopMidpoint(x: float, y: float, z: float) -> Vector:
    return Vector((x, y, z))


@dataclasses.dataclass(frozen=True)
class SimpleMarkerInfo:
    recognition_object: WebotsRecognitionObject
    size_m: float = 0.2


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
                    orientation=ApproximateOrientation(0, 0, 0),
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

    def test_simple_orientations(self) -> None:
        QUARTER_PI = ApproximateFloat(math.pi / 4)
        UNIT_DIAGONAL = ApproximateFloat(1 / math.sqrt(2))

        HALF_WIDTH = ApproximateFloat(SimpleMarkerInfo.size_m / 2)
        HALF_DIAGONAL = ApproximateFloat(HALF_WIDTH / math.sqrt(2))
        HALF_THICKNESS = ApproximateFloat(0.0001 / 2)
        HALF_DIAG_THICKNESS = ApproximateFloat(HALF_THICKNESS / math.sqrt(2))

        ORIENTATIONS = [
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/all0.png
                'camera-marker-straight-ahead',
                Normal(-1, 0, 0),
                TopMidpoint(-HALF_THICKNESS, 0, HALF_WIDTH),
                Orientation(
                    yaw=0,
                    pitch=0,
                    roll=0,
                ),
                2,
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/yaw-45.png
                'camera-marker-turned-right',
                Normal(-UNIT_DIAGONAL, -UNIT_DIAGONAL, 0),
                TopMidpoint(-HALF_DIAG_THICKNESS, -HALF_DIAG_THICKNESS, HALF_WIDTH),
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=0,
                    roll=0,
                ),
                10,
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/yaw45.png
                'camera-marker-turned-left',
                Normal(-UNIT_DIAGONAL, UNIT_DIAGONAL, 0),
                TopMidpoint(-HALF_DIAG_THICKNESS, HALF_DIAG_THICKNESS, HALF_WIDTH),
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=0,
                    roll=0,
                ),
                11,
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/pitch45.png
                'camera-marker-leaning-back',
                Normal(-UNIT_DIAGONAL, 0, UNIT_DIAGONAL),
                TopMidpoint(
                    ApproximateFloat(HALF_DIAGONAL - HALF_DIAG_THICKNESS),
                    0,
                    ApproximateFloat(HALF_DIAGONAL + HALF_DIAG_THICKNESS),
                ),
                Orientation(
                    yaw=0,
                    pitch=QUARTER_PI,
                    roll=0,
                ),
                12,
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/pitch-45.png
                'camera-marker-leaning-forwards',
                Normal(-UNIT_DIAGONAL, 0, -UNIT_DIAGONAL),
                TopMidpoint(
                    ApproximateFloat(-HALF_DIAGONAL - HALF_DIAG_THICKNESS),
                    0,
                    ApproximateFloat(HALF_DIAGONAL - HALF_DIAG_THICKNESS),
                ),
                Orientation(
                    yaw=0,
                    pitch=-QUARTER_PI,
                    roll=0,
                ),
                13,
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/roll45.png
                'camera-marker-leaning-left',
                Normal(-1, 0, 0),
                TopMidpoint(-HALF_THICKNESS, HALF_DIAGONAL, HALF_DIAGONAL),
                Orientation(
                    yaw=0,
                    pitch=0,
                    roll=QUARTER_PI,
                ),
                14,
            ),
            (
                # https://studentrobotics.org/docs/images/content/vision/orientation/roll-45.png
                'camera-marker-leaning-right',
                Normal(-1, 0, 0),
                TopMidpoint(-HALF_THICKNESS, -HALF_DIAGONAL, HALF_DIAGONAL),
                Orientation(
                    yaw=0,
                    pitch=0,
                    roll=-QUARTER_PI,
                ),
                15,
            ),
        ]

        for name, normal, top_midpoint, orientation, marker_id in ORIENTATIONS:
            with self.subTest(name):
                camera = self.get_camera(name)

                obj, = camera.camera.getRecognitionObjects()

                (fiducial_marker, _), = markers_from_objects(
                    [SimpleMarkerInfo(recognition_object=obj)],
                )

                self.assertEqual(
                    normal,
                    fiducial_marker.normal(),
                    f"Wrong normal (model: {obj.getModel()})",
                )

                self.assertEqual(
                    top_midpoint,
                    fiducial_marker.top_midpoint(),
                    f"Wrong top midpoint (model: {obj.getModel()})",
                )

                marker, = camera.see()
                self.assertEqual(
                    marker_id,
                    marker.id,
                    f"Wrong marker id (self check failed, model: {obj.getModel()})",
                )

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

    def test_multi_orientations(self) -> None:
        QUARTER_PI = ApproximateFloat(math.pi / 4)

        ORIENTATIONS = [
            # START_GENERATED:ORIENTATIONS
            (
                'camera-marker-pos-pitch-pos-roll',
                Orientation(
                    yaw=0,
                    pitch=QUARTER_PI,
                    roll=QUARTER_PI,
                ),
                0,
            ),
            (
                'camera-marker-pos-pitch-neg-roll',
                Orientation(
                    yaw=0,
                    pitch=QUARTER_PI,
                    roll=-QUARTER_PI,
                ),
                1,
            ),
            (
                'camera-marker-neg-pitch-pos-roll',
                Orientation(
                    yaw=0,
                    pitch=-QUARTER_PI,
                    roll=QUARTER_PI,
                ),
                2,
            ),
            (
                'camera-marker-neg-pitch-neg-roll',
                Orientation(
                    yaw=0,
                    pitch=-QUARTER_PI,
                    roll=-QUARTER_PI,
                ),
                3,
            ),
            (
                'camera-marker-pos-yaw-pos-roll',
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=0,
                    roll=QUARTER_PI,
                ),
                4,
            ),
            (
                'camera-marker-pos-yaw-neg-roll',
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=0,
                    roll=-QUARTER_PI,
                ),
                5,
            ),
            (
                'camera-marker-pos-yaw-pos-pitch',
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=QUARTER_PI,
                    roll=0,
                ),
                6,
            ),
            (
                'camera-marker-pos-yaw-pos-pitch-pos-roll',
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=QUARTER_PI,
                    roll=QUARTER_PI,
                ),
                7,
            ),
            (
                'camera-marker-pos-yaw-pos-pitch-neg-roll',
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=QUARTER_PI,
                    roll=-QUARTER_PI,
                ),
                8,
            ),
            (
                'camera-marker-pos-yaw-neg-pitch',
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=-QUARTER_PI,
                    roll=0,
                ),
                9,
            ),
            (
                'camera-marker-pos-yaw-neg-pitch-pos-roll',
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=-QUARTER_PI,
                    roll=QUARTER_PI,
                ),
                10,
            ),
            (
                'camera-marker-pos-yaw-neg-pitch-neg-roll',
                Orientation(
                    yaw=QUARTER_PI,
                    pitch=-QUARTER_PI,
                    roll=-QUARTER_PI,
                ),
                11,
            ),
            (
                'camera-marker-neg-yaw-pos-roll',
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=0,
                    roll=QUARTER_PI,
                ),
                12,
            ),
            (
                'camera-marker-neg-yaw-neg-roll',
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=0,
                    roll=-QUARTER_PI,
                ),
                13,
            ),
            (
                'camera-marker-neg-yaw-pos-pitch',
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=QUARTER_PI,
                    roll=0,
                ),
                14,
            ),
            (
                'camera-marker-neg-yaw-pos-pitch-pos-roll',
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=QUARTER_PI,
                    roll=QUARTER_PI,
                ),
                15,
            ),
            (
                'camera-marker-neg-yaw-pos-pitch-neg-roll',
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=QUARTER_PI,
                    roll=-QUARTER_PI,
                ),
                16,
            ),
            (
                'camera-marker-neg-yaw-neg-pitch',
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=-QUARTER_PI,
                    roll=0,
                ),
                17,
            ),
            (
                'camera-marker-neg-yaw-neg-pitch-pos-roll',
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=-QUARTER_PI,
                    roll=QUARTER_PI,
                ),
                18,
            ),
            (
                'camera-marker-neg-yaw-neg-pitch-neg-roll',
                Orientation(
                    yaw=-QUARTER_PI,
                    pitch=-QUARTER_PI,
                    roll=-QUARTER_PI,
                ),
                19,
            ),
            # END_GENERATED:ORIENTATIONS
        ]

        for name, orientation, marker_id in ORIENTATIONS:
            with self.subTest(name):
                camera = self.get_camera(name)

                obj, = camera.camera.getRecognitionObjects()

                marker, = camera.see()
                self.assertEqual(
                    marker_id,
                    marker.id,
                    f"Wrong marker id (self check failed, model: {obj.getModel()})",
                )

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
