import re
import time
from enum import Enum
from typing import List, Optional, NamedTuple

from sr.robot.vision import (
    Face,
    Vector,
    PolarCoord,
    Orientation,
    tokens_from_objects,
    polar_from_cartesian,
)
from sr.robot.settings import TIME_STEP

Cartesian = NamedTuple("Cartesian", (
    ("x", float),
    ("y", float),
    ("z", float),
))

# Note: we cannot suport `image` coordinates for now.
Point = NamedTuple('Point', (
    ('world', Cartesian),
    ('polar', PolarCoord),
))

MARKER_MODEL_RE = re.compile(r"^[AGS]\d{0,2}$")


class MarkerType(Enum):
    ARENA = "ARENA"
    GOLD = "TOKEN_GOLD"
    SILVER = "TOKEN_SILVER"

# Existing token types
MARKER_ARENA = MarkerType.ARENA
MARKER_TOKEN_GOLD = MarkerType.GOLD
MARKER_TOKEN_SILVER = MarkerType.SILVER

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


def parse_marker_info(model_id: str) -> Optional[MarkerInfo]:
    """
    Parse the model id of a maker model into a `MarkerInfo`.

    Expected input format is a letter and two digits. The letter indicates the
    type of the marker, the digits its "libkoki" 'code'.

    Examples: 'A00', 'A01', ..., 'G32', 'G33', ..., 'S40', 'S41', ...
    """

    match = MARKER_MODEL_RE.match(model_id)
    if match is None:
        return None

    kind, number = model_id[0], model_id[1:]

    marker_type = MARKER_MODEL_TYPE_MAP[kind]
    code = int(number)

    type_offset = MARKER_TYPE_OFFSETS[marker_type]

    return MarkerInfo(
        code=code,
        marker_type=marker_type,
        offset=code - type_offset,
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

    @staticmethod
    def _build_point(vector: Vector) -> Point:
        return Point(
            world=Cartesian(*vector.data),
            polar=polar_from_cartesian(vector),
        )

    @property
    def centre(self) -> Point:
        return self._build_point(self._face.centre_global())

    @property
    def vertices(self) -> List[Point]:
        # Note quite the black corners of the marker, though fairly close --
        # actually the corners of the face of the modelled token.
        return [self._build_point(x) for x in self._face.corners_global().values()]

    @property
    def dist(self) -> float:
        return self._face.centre_global().magnitude()

    @property
    def rot_y(self) -> float:
        return self.centre.polar.rot_y

    @property
    def orientation(self) -> Orientation:
        return self._face.orientation()


class Camera:
    def __init__(self, webot):
        self.webot = webot
        self.camera = self.webot.getCamera("camera")
        self.camera.enable(TIME_STEP)
        self.camera.recognitionEnable(TIME_STEP)

    def see(self) -> List[Marker]:
        object_infos = {}

        for recognition_object in self.camera.getRecognitionObjects():
            marker_info = parse_marker_info(
                recognition_object.get_model().decode(),
            )
            if marker_info:
                object_infos[recognition_object] = marker_info

        tokens = tokens_from_objects(
            object_infos.keys(),
            lambda o: object_infos[o].size,
        )

        when = time.time()

        markers = []

        for token, recognition_object in tokens:
            marker_info = object_infos[recognition_object]
            is_2d = marker_info.marker_type == MarkerType.ARENA
            for face in token.visible_faces(is_2d=is_2d):
                markers.append(Marker(face, marker_info, when))

        return markers
