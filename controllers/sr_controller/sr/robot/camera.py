import re
import time
from enum import Enum
from math import degrees
from collections import namedtuple

from sr.robot.vision import Face, tokens_from_objects
from sr.robot.settings import TIME_STEP
from sr.robot.randomizer import add_jitter

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

MARKER_MODEL_RE = re.compile(rb"^[AGS]\d{2}$")


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
    def __init__(self, face: Face, model: str) -> None:
        self._face = face
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
        return Position([position_jitter(pos) for pos in self._face.centre_global().data])

    @property
    def orientation(self):
        return self._face.orientation()


class Camera:
    def __init__(self, webot):
        self.webot = webot
        self.camera = self.webot.getCamera("camera")
        self.camera.enable(TIME_STEP)
        self.camera.recognitionEnable(TIME_STEP)

    def see(self):
        objects = [
            recognition_object
            for recognition_object in self.camera.getRecognitionObjects()
            if MARKER_MODEL_RE.match(recognition_object.get_model())
        ]

        tokens = tokens_from_objects(objects)

        markers = [
            Marker(face, recognition_object.get_model().decode())
            for token, recognition_object in tokens
            for face in token.visible_faces()
        ]

        time.sleep(0.1 * len(markers))

        return markers
