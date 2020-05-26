import re
import time
from enum import Enum
from math import degrees
from typing import Optional, NamedTuple
from collections import namedtuple

from sr.robot.vision import Face, tokens_from_objects
from sr.robot.settings import TIME_STEP
from sr.robot.randomizer import add_jitter

Cartesian = namedtuple("Cartesian", ["x", "y", "z"])

# TODO: support `polar` here.
# Note: we cannot suport `image` coordinates for now.
Point = namedtuple('Point', ('world',))

MARKER_MODEL_RE = re.compile(r"^[AGS]\d{2}$")


class MarkerType(Enum):
    ARENA = "ARENA"
    GOLD = "TOKEN_GOLD"
    SILVER = "TOKEN_SILVER"


MarkerInfo = NamedTuple('MarkerInfo', (
    ('code', int),
    ('marker_type', MarkerType),
    ('offset', int),
    ('size', float),
))


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


def parse_marker_info(model_id: str) -> Optional[MarkerInfo]:
    match = MARKER_MODEL_RE.match(model_id)
    if match is None:
        return None

    kind, number = model_id[0], model_id[1:]

    marker_type = MARKER_MODEL_TYPE_MAP[kind]
    offset = int(number)

    return MarkerInfo(
        code=MARKER_TYPE_OFFSETS[marker_type] + offset,
        marker_type=marker_type,
        offset=offset,
        size=MARKER_TYPE_SIZE[marker_type],
    )


class Marker:
    # Note: properties in the same order as in the docs.
    # Note: we are _not_ supporting image-related properties, so no `res`.

    def __init__(self, face: Face, marker_info: MarkerInfo, timestamp: float) -> None:
        self._face = face

        self.info = marker_info
        self.timestamp = timestamp

    def __str__(self) -> str:
        return '<Marker: {}>'.format(', '.join((
            'info={}'.format(self.info),
            'centre={}'.format(self.centre),
            'dist={}'.format(self.dist),
            'orientation={}'.format(self.orientation),
        )))

    @property
    def centre(self):
        return Point(
            world=Cartesian(*self._face.centre_global().data),
        )

    @property
    def vertices(self):
        # Note quite the black corners of the marker, though fairly close --
        # actually the corners of the face of the modelled token.
        return [Cartesian(*x.data) for x in self._face.corners_global().values()]

    @property
    def dist(self) -> float:
        return self._face.centre_global().magnitude()

    # TODO: rot_y

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
        objects = {}

        for recognition_object in self.camera.getRecognitionObjects():
            marker_info = parse_marker_info(
                recognition_object.get_model().decode(),
            )
            if marker_info:
                objects[recognition_object] = marker_info

        tokens = tokens_from_objects(objects.keys())

        when = time.time()

        markers = [
            Marker(face, objects[recognition_object], when)
            for token, recognition_object in tokens
            for face in token.visible_faces()
        ]

        time.sleep(0.1 * len(markers))

        return markers
