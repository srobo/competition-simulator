import re
import time
from enum import Enum
from math import degrees
from collections import namedtuple

from sr.robot.settings import TIME_STEP
from sr.robot.randomizer import add_jitter

Orientation = namedtuple("Orientation", ["rot_x", "rot_y", "rot_z"])
Position = namedtuple("Position", ["x", "y", "z"])

MarkerInfo = namedtuple('MarkerInfo', (
    'code',
    'marker_type',
    'offset',
    'size',
))

# TODO: support `polar` here.
# Note: we cannot suport `image` coordinates for now.
Point = namedtuple('Point', ('world',))

MARKER_MODEL_RE = re.compile(r"^[AGS]\d{2}$")


class MarkerType(Enum):
    ARENA = "ARENA"
    GOLD = "TOKEN_GOLD"
    SILVER = "TOKEN_SILVER"


MARKER_MODEL_TYPE_MAP = {
    'A': MarkerType.ARENA,
    'G': MarkerType.GOLD,
    'S': MarkerType.SILVER,
}

MARKER_TYPE_OFFSETS = {
    MarkerType.ARENA: 0,
    MarkerType.GOLD: 32,
    MarkerType.SILVER: 40,
}

MARKER_TYPE_SIZE = {
    MarkerType.ARENA: 0.25,
    MarkerType.GOLD: 0.2,
    MarkerType.SILVER: 0.2,
}


def degrees_jitter(radians):
    return add_jitter(degrees(radians), -180, 180)


def position_jitter(pos):
    return add_jitter(pos, 0, 5.75)


class Marker:
    def __init__(self, recognition_object, model):
        self._recognition_object = recognition_object
        self._model = model

    @property
    def info(self):
        kind, number = self._model[0], self._model[1:]

        marker_type = MARKER_MODEL_TYPE_MAP[kind]
        offset = int(number)

        return MarkerInfo(
            code=MARKER_TYPE_OFFSETS[marker_type] + offset,
            marker_type=marker_type,
            offset=offset,
            size=MARKER_TYPE_SIZE[marker_type],
        )

    @property
    def position(self):
        return Position([position_jitter(pos) for pos in self._recognition_object.get_position()])

    @property
    def orientation(self):
        x, y, z, t = self._recognition_object.get_orientation()
        x *= t
        y *= t
        z *= t
        return Orientation(degrees_jitter(x), degrees_jitter(y), degrees_jitter(z))

    @property
    def size(self):
        return 0.25 if self.type == MarkerType.ARENA else 0.2


class Camera:
    def __init__(self, webot):
        self.webot = webot
        self.camera = self.webot.getCamera("camera")
        self.camera.enable(TIME_STEP)
        self.camera.recognitionEnable(TIME_STEP)

    def see(self):
        marker = []

        for recognition_object in self.camera.getRecognitionObjects():
            model = recognition_object.get_model().decode()
            if MARKER_MODEL_RE.match(model):
                marker.append(Marker(recognition_object, model))

        time.sleep(0.1 * len(marker))

        return marker
