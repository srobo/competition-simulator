from sr.robot.settings import TIME_STEP
from collections import namedtuple
from math import degrees


Orientation = namedtuple("Orientation", ["rot_x", "rot_y", "rot_z"])
Position = namedtuple("Position", ["x", "y", "z"])

TOKEN_GOLD = "TOKEN_GOLD"
TOKEN_SILVER = "TOKEN_SILVER"


class Token:
    def __init__(self, recognition_object):
        self._recognition_object = recognition_object

    def _get_color_id(self):
        model = self._recognition_object.get_model
        return model[0], model[1:]

    @property
    def id(self):
        return int(self._get_color_id()[1])

    @property
    def type(self):
        return {
            'S': TOKEN_SILVER,
            'G': TOKEN_GOLD
        }[self._get_color_id()[0]]

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


class Camera:
    def __init__(self, webot):
        self.webot = webot
        self.camera = self.webot.getCamera("camera")
        self.camera.enable(TIME_STEP)
        self.camera.width = 800
        self.camera.height = 600
        self.camera.recognitionEnable(TIME_STEP)

    def see(self):
        return [
            Token(recognition_object)
            for recognition_object in self.camera.getRecognitionObjects()
        ]
