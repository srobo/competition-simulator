from __future__ import annotations

import re
import enum
import threading
from typing import Container, NamedTuple

from controller import Robot, Camera as WebotCamera
from sr.robot3.vision import Face, Orientation, tokens_from_objects
from sr.robot3.coordinates import Point

from .utils import maybe_get_robot_device

MARKER_MODEL_RE = re.compile(r"^[FB]\d{0,2}$")


# Zoloto's markers API doesn't expose any information derived from the marker's
# identity, however we need to track whether the marker is of a kind that would
# be on a box or a wall and its size. This enum lets us do that.
class ObjectType(enum.Enum):
    FLAT = 'F'
    BOX = 'B'


class MarkerInfo(NamedTuple):
    code: int
    size: int
    object_type: ObjectType


MARKER_SIZES: dict[Container[int], int] = {
    range(28): 200,  # 0 - 27 for arena boundary
    range(28, 100): 100,  # Everything else is a token
}


def get_marker_size(marker_id: int) -> int:
    for bucket, size in MARKER_SIZES.items():
        if marker_id in bucket:
            return size

    raise ValueError(f"Unknown marker id {marker_id}")


def parse_marker_info(model_id: str) -> MarkerInfo | None:
    """
    Parse the model id of a maker model into a `MarkerInfo`.

    Expected input format is a letter and two digits. The letter indicates the
    type of the marker, indicating whether or not the marker is on a flat
    object. The digits which form the 'code' are used for determining the
    properties visible in the API.

    Examples: 'F00', 'F01', ..., 'B32', 'B33', ...
    """

    match = MARKER_MODEL_RE.match(model_id)
    if match is None:
        return None

    kind, number = model_id[0], model_id[1:]

    code = int(number)

    return MarkerInfo(
        code=code,
        size=get_marker_size(code),
        object_type=ObjectType(kind),
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
            f'info={self.info}',
            f'centre={self.centre}',
            f'dist={self.dist}',
            f'orientation={self.orientation}',
        )))

    @property
    def centre(self) -> Point:
        """A `Point` describing the position of the centre of the marker."""
        return Point.from_vector(self._face.centre_global())

    @property
    def vertices(self) -> list[Point]:
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
    def __init__(self, webot: Robot, camera: WebotCamera, lock: threading.Lock) -> None:
        self._webot = webot
        self._timestep = int(webot.getBasicTimeStep())

        self.camera = camera
        self.camera.enable(self._timestep)
        self.camera.recognitionEnable(self._timestep)

        self._lock = lock

    def see(self, *, eager: bool = True) -> list[Marker]:
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

    def _see(self) -> list[Marker]:
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
            is_2d = marker_info.object_type == ObjectType.FLAT
            for face in token.visible_faces(is_2d=is_2d):
                markers.append(Marker(face, marker_info, when))

        return markers

    def see_ids(self) -> list[int]:
        # While in theory this method ought to be the "fast" method, processing
        # speed doesn't matter much in the simulator and with the locking we
        # need to do it's much easier to let this be a shallow wrapper around
        # the full implementation.
        return [x.info.code for x in self.see()]

    # The simulator does not emulate the `capture` or `save` methods.


def init_cameras(webot: Robot, lock: threading.Lock) -> list[Camera]:
    camera = maybe_get_robot_device(webot, 'camera', WebotCamera)
    if camera is None:
        return []
    return [Camera(webot, camera, lock)]
