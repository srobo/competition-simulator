import re
import time
from enum import Enum
from math import degrees
from collections import namedtuple

from sr.robot.settings import TIME_STEP
from sr.robot.randomizer import add_jitter

Orientation = namedtuple("Orientation", ["rot_x", "rot_y", "rot_z"])
Position = namedtuple("Position", ["x", "y", "z"])

MARKER_MODEL_RE = re.compile(r"^[AGS]\d{2}$")


class MarkerType(Enum):
    ARENA = "ARENA"
    GOLD = "TOKEN_GOLD"
    SILVER = "TOKEN_SILVER"


def degrees_jitter(radians):
    return add_jitter(degrees(radians), -180, 180)


def position_jitter(pos):
    return add_jitter(pos, 0, 5.75)


class Marker:
    def __init__(self, recognition_object, model):
        self._recognition_object = recognition_object
        self._model = model

    def _get_type_and_id(self):
        model = self._model
        return model[0], model[1:]

    @property
    def id(self):
        return int(self._get_type_and_id()[1])

    @property
    def type(self):
        type = self._get_type_and_id()[0]
        if type == "S":
            return MarkerType.SILVER
        elif type == "G":
            return MarkerType.GOLD
        elif type == "A":
            return MarkerType.ARENA
        raise ValueError("Unknown type {}.".format(type))

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
