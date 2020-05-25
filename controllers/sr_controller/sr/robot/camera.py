from sr.robot.settings import TIME_STEP
from sr.robot.randomizer import random_in_range, add_jitter
from collections import namedtuple
from math import degrees
from enum import Enum
import re
import time


Orientation = namedtuple("Orientation", ["rot_x", "rot_y", "rot_z"])
Position = namedtuple("Position", ["x", "y", "z"])

TOKEN_MODEL_RE = re.compile(r"^[AGS]\d{2}$")


class TokenType(Enum):
    GOLD = "TOKEN_GOLD"
    SILVER = "TOKEN_SILVER"
    ARENA = "TOKEN_ARENA"


def degrees_jitter(radians):
    return add_jitter(degrees(radians), -180, 180)


def position_jitter(pos):
    return add_jitter(pos, 0, 5.75)


class Token:
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
            return TokenType.SILVER
        elif type == "G":
            return TokenType.GOLD
        elif type == "A":
            return TokenType.ARENA
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
        return 0.25 if self.type == TokenType.ARENA else 0.2


class Camera:
    def __init__(self, webot):
        self.webot = webot
        self.camera = self.webot.getCamera("camera")
        self.camera.enable(TIME_STEP)
        self.camera.recognitionEnable(TIME_STEP)

    def see(self):
        tokens = []
        for recognition_object in self.camera.getRecognitionObjects():
            model = recognition_object.get_model().decode()
            if TOKEN_MODEL_RE.match(model):
                tokens.append(Token(recognition_object, model))
        time.sleep(0.1 * len(tokens))
        return tokens
