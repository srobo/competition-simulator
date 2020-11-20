import re
import threading
from enum import Enum
from typing import List, Optional, NamedTuple

from controller import Robot
from sr.robot.vision import Face, Orientation, tokens_from_objects
from sr.robot.coordinates import Point

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

    def __repr__(self) -> str:
        return '<Marker: {}>'.format(', '.join((
            'info={}'.format(self.info),
            'centre={}'.format(self.centre),
            'dist={}'.format(self.dist),
            'orientation={}'.format(self.orientation),
        )))

    @property
    def centre(self) -> Point:
        """A `Point` describing the position of the centre of the marker."""
        return Point.from_vector(self._face.centre_global())

    @property
    def vertices(self) -> List[Point]:
        """
        A list of 4 `Point` instances, each representing the position of the
        black corners of the marker.
        """
        # Note quite the black corners of the marker, though fairly close --
        # actually the corners of the face of the modelled token.
        return [Point.from_vector(x) for x in self._face.corners_global().values()]

    @property
    def dist(self) -> float:
        """An alias for `centre.polar.length`."""
        return self._face.centre_global().magnitude()

    @property
    def rot_y(self) -> float:
        """An alias for `centre.polar.rot_y`."""
        return self.centre.polar.rot_y

    @property
    def orientation(self) -> Orientation:
        """An `Orientation` instance describing the orientation of the marker."""
        return self._face.orientation()


class Camera:
    def __init__(self, webot: Robot, lock: threading.Lock) -> None:
        self._webot = webot
        self._timestep = int(webot.getBasicTimeStep())

        self.camera = webot.getCamera("camera")
        self.camera.enable(self._timestep)
        self.camera.recognitionEnable(self._timestep)

        self._lock = lock

    def see(self) -> List[Marker]:
        """
        Identify items which the camera can see and return a list of `Marker`
        instances describing them.
        """
        # Webots appears not to like it if you try to hang on to a
        # `CameraRecognitionObject` after another time-step has passed. However
        # because we advance the time-steps in a background thread we're likely
        # to do that all the time. In order to counter that we have our `Robot`
        # pass down its time-step lock so that we can hold that while we do the
        # processing. The objects which we pass back to the caller are safe to
        # use because they don't refer to Webots' objects at all.
        with self._lock:
            self._webot.step(self._timestep)
            return self._see()

    def _see(self) -> List[Marker]:
        object_infos = {}

        for recognition_object in self.camera.getRecognitionObjects():
            marker_info = parse_marker_info(
                recognition_object.get_model().decode(errors='replace'),
            )
            if marker_info:
                object_infos[recognition_object] = marker_info

        tokens = tokens_from_objects(
            object_infos.keys(),
            lambda o: object_infos[o].size,
        )

        when = self._webot.getTime()

        markers = []

        for token, recognition_object in tokens:
            marker_info = object_infos[recognition_object]
            is_2d = marker_info.marker_type == MarkerType.ARENA
            for face in token.visible_faces(is_2d=is_2d):
                markers.append(Marker(face, marker_info, when))

        return markers
