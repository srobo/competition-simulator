from sr.robot.settings import TIME_STEP
from collections import namedtuple
from math import degrees
from enum import Enum
import re


Orientation = namedtuple("Orientation", ["rot_x", "rot_y", "rot_z"])
Position = namedtuple("Position", ["x", "y", "z"])

TOKEN_MODEL_RE = re.compile(r"^[SG]\d{2}$")


class TokenType(Enum):
    GOLD = "TOKEN_GOLD"
    SILVER = "TOKEN_SILVER"


class Token:
    def __init__(self, recognition_object, model):
        self._recognition_object = recognition_object
        self._model = model

    def _get_colour_id(self):
        model = self._model
        return model[0], model[1:]

    @property
    def id(self):
        return int(self._get_colour_id()[1])

    @property
    def type(self):
        colour = self._get_colour_id()[0]
        if colour == "S":
            return TokenType.SILVER
        elif colour == "G":
            return TokenType.GOLD
        raise ValueError("Unknown colour {}.".format(colour))

    @property
    def position(self):
        return Position(*self._recognition_object.get_position())

    @property
    def orientation(self):
        x, y, z, t = self._recognition_object.get_orientation()
        x *= t
        y *= t
        z *= t
        return Orientation(degrees(x), degrees(y), degrees(z))

    @property
    def size(self):
        return 0.2


class Camera:
    def __init__(self, webot):
        self.webot = webot
        self.camera = self.webot.getCamera("camera")
        self.camera.enable(TIME_STEP)
        self.camera.width = 800
        self.camera.height = 600
        self.camera.recognitionEnable(TIME_STEP)

    def see(self):
        tokens = []
        for recognition_object in self.camera.getRecognitionObjects():
            model = recognition_object.get_model().decode()
            if TOKEN_MODEL_RE.match(model):
                tokens.append(Token(recognition_object, model))
        return tokens
