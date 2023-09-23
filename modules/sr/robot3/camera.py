from __future__ import annotations

import re
import threading
from typing import Container, NamedTuple

from controller import (
    Robot,
    Camera as WebotCamera,
    CameraRecognitionObject as WebotsRecognitionObject,
)
from sr.robot3.vision import Orientation, markers_from_objects
from sr.robot3.coordinates import Position

from .utils import maybe_get_robot_device

MARKER_MODEL_RE = re.compile(r'^F(?P<id>\d{1,2})$')


class MarkerInfo(NamedTuple):
    recognition_object: WebotsRecognitionObject

    code: int
    size_mm: int

    @property
    def size_m(self) -> float:
        # Webots uses metres.
        return self.size_mm / 1000


MARKER_SIZES: dict[Container[int], int] = {
    range(28): 200,  # 0 - 27 for arena boundary
    range(28, 100): 100,  # Everything else is a token
}


def get_marker_size_mm(marker_id: int) -> int:
    """
    Return the marker size in millimetres.
    """
    for bucket, size in MARKER_SIZES.items():
        if marker_id in bucket:
            return size

    raise ValueError(f"Unknown marker id {marker_id}")


def parse_marker_info(recognition_object: WebotsRecognitionObject) -> MarkerInfo | None:
    """
    Parse the model id of a maker model into a `MarkerInfo`.

    Expected input format is a letter and two digits. The letter indicates the
    type of the marker, indicating whether or not the marker is on a flat
    object. The digits which form the 'code' are used for determining the
    properties visible in the API.

    Examples: 'F00', 'F01', ...
    """

    match = MARKER_MODEL_RE.match(recognition_object.getModel())
    if match is None:
        return None

    code = int(match['id'])

    return MarkerInfo(
        recognition_object=recognition_object,
        code=code,
        size_mm=get_marker_size_mm(code),
    )


class Marker(NamedTuple):
    """
    Wrapper of a marker detection with axis and rotation calculated.

    :param id: The ID of the detected marker
    :param size: The physical size of the marker in millimetres
    :param position: Position information of the marker relative to the camera
    :param orientation: Orientation information of the marker
    """

    id: int  # noqa: A003 # match kit
    size: int

    # Note: we are _not_ supporting image-related properties, so no `pixel_*`.

    position: Position = Position(0, 0, 0)
    orientation: Orientation = Orientation(0, 0, 0)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} distance={self.position.distance:.0f}mm "
            f"horizontal_angle={self.position.horizontal_angle:.2f}rad "
            f"vertical_angle={self.position.vertical_angle:.2f}rad size={self.size}mm>"
        )


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
        marker_infos = []

        for recognition_object in self.camera.getRecognitionObjects():
            marker_info = parse_marker_info(recognition_object)
            if marker_info:
                marker_infos.append(marker_info)

        fiducial_markers = markers_from_objects(marker_infos)

        markers = [
            Marker(
                id=marker_info.code,
                size=marker_info.size_mm,
                position=Position.from_cartesian_metres(
                    fiducial_marker.position.data,  # type: ignore[arg-type]
                ),
                orientation=fiducial_marker.orientation(),
            )
            for fiducial_marker, marker_info in fiducial_markers
        ]
        return markers

    # The simulator does not emulate the `capture` or `save` methods.


def init_cameras(webot: Robot, lock: threading.Lock) -> list[Camera]:
    camera = maybe_get_robot_device(webot, 'camera', WebotCamera)
    if camera is None:
        return []
    return [Camera(webot, camera, lock)]
