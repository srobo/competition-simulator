from __future__ import annotations

import logging
import threading
from typing import Iterable, Iterator, NamedTuple
from pathlib import Path
from contextlib import contextmanager
from collections import defaultdict

from controller import Robot as WebotsRobot, Camera as WebotsCamera

from .utils import maybe_get_robot_device
from .marker import Marker

LOGGER = logging.getLogger(__name__)

MARKER_SIZES: dict[Iterable[int], int] = {
    range(28): 200,  # 0 - 27 for arena boundary
    range(28, 100): 80,  # Everything else is a token
}


class Recognition(NamedTuple):
    marker_id: int
    # X forward, Y left, Z up
    pose_t: tuple[float, float, float]
    # In axis-angle form
    pose_R: tuple[float, float, float, float]
    pixel_center: tuple[int, int]


class WebotsCameraBoard:
    """
    Virtual Camera Board for detecting recognition objects.

    Additionally, it will do pose estimation, along with the spatial
    positon and orientation of the markers that it has detected.
    """

    name: str = "Webots Camera Board"

    def __init__(
        self,
        robot: WebotsRobot,
        camera: WebotsCamera,
        lock: threading.Lock,
        marker_sizes: dict[Iterable[int], int],
        fps: int = 30,
    ):
        self._sample_time = 1000 // fps
        self._serial = f"Webots Camera - {camera.getName()}"
        self._marker_offset = 0
        self._tag_sizes: dict[int, float] = {}

        self._camera = camera
        self._robot = robot
        self._lock = lock

        self._set_marker_sizes(marker_sizes)

    @property
    def serial_number(self) -> str:
        """Get the serial number."""
        return self._serial

    @property
    def firmware_version(self) -> str | None:
        """Get the firmware version of the board."""
        return '1.0'

    def see(self, *, eager: bool = True) -> list[Marker]:
        """
        Capture an image and identify fiducial markers.

        :param eager: Process the pose estimations of markers immediately,
            currently unused.
        :returns: list of markers that the camera could see.
        """
        raw_markers: list[Marker] = []
        recognition_objects: dict[str, dict[str, Recognition]] = defaultdict(dict)

        with self._capture():
            for recognition_object in self._camera.getRecognitionObjects():
                # Get the object's assigned "model" value, the marker has 5 detection points:
                # the marker itself and the 4 corners, named in the form <id>_<location>
                tag_uid, tag_name, tag_point = str(recognition_object.getModel()).split('_')

                try:
                    marker_id = int(tag_name)
                except ValueError:
                    LOGGER.warning(f"Invalid marker id found: {tag_name}")
                    continue

                pose_t = tuple(recognition_object.getPosition())
                pose_R = tuple(recognition_object.getOrientation())
                pixel_center = tuple(recognition_object.getPositionOnImage())

                recognition_objects[tag_uid][tag_point] = Recognition(
                    marker_id=marker_id,
                    pose_t=pose_t,  # type: ignore[arg-type]
                    pose_R=pose_R,  # type: ignore[arg-type]
                    pixel_center=pixel_center,  # type: ignore[arg-type]
                )

        for marker_points in recognition_objects.values():
            if marker_points.keys() != {'base', 'TL', 'TR', 'BL', 'BR'}:
                LOGGER.debug(f"Only partially saw {marker_id}.")
                continue

            size = self._tag_sizes.get(marker_points['base'].marker_id, 0)

            raw_markers.append(Marker(
                id=marker_points['base'].marker_id,
                # X forward, Y left, Z up
                pose_t=marker_points['base'].pose_t,
                # In axis-angle form
                pose_R=marker_points['base'].pose_R,
                tag_size=size,
                pixel_center=marker_points['base'].pixel_center,
                pixel_corners=[
                    marker_points['TL'].pixel_center,
                    marker_points['TR'].pixel_center,
                    marker_points['BL'].pixel_center,
                    marker_points['BR'].pixel_center,
                ],
            ))

        return self._marker_filter(raw_markers)

    def see_ids(self) -> list[int]:
        """
        Capture an image and identify fiducial markers.

        This method returns just the marker IDs that are visible.
        :returns: A list of IDs for the markers that were visible.
        """
        return [marker.id for marker in self.see()]

    def save(self, path: Path | str) -> None:
        """
        Save an unannotated image to a path.

        NOTE This differs from the kit version as the image is not annotated.
        """
        path = Path(path)
        if not path.suffix:
            LOGGER.warning("No file extension given, defaulting to jpg")
            path = path.with_suffix(".jpg")
        # TODO check this is within the folder

        with self._capture():
            self._camera.saveImage(str(path), 100)

    @contextmanager
    def _capture(self) -> Iterator[None]:
        """
        A context manager to handle enabling and disabling the camera and recognition.

        Handles waiting for the camera to be sampled.
        """
        # Hold the step lock both to allow us to wait for the camera's sampling
        # period and remain in the resulting timestap while the recognition
        # objects are used.
        with self._lock:
            try:
                self._camera.enable(self._sample_time)
                self._camera.recognitionEnable(self._sample_time)
                self._robot.step(self._sample_time)
                yield
            finally:
                self._camera.recognitionDisable()
                self._camera.disable()

    def _set_marker_sizes(
        self,
        marker_sizes: dict[Iterable[int], int],
        marker_offset: int = 0,
    ) -> None:
        """Set the sizes of all the markers used in the game."""
        # store marker offset to be used by the filter
        self._marker_offset = marker_offset
        # Reset previously stored sizes
        self._tag_sizes = {}
        for marker_ids, marker_size in marker_sizes.items():
            # Unroll generators to give direct lookup
            for marker_id in marker_ids:
                # Convert to meters
                self._tag_sizes[marker_id + marker_offset] = float(marker_size) / 1000

    def _marker_filter(self, markers: list[Marker]) -> list[Marker]:
        """Apply marker offset and remove markers that are not in the game."""
        filtered_markers: list[Marker] = []

        for marker in markers:
            if marker._id in self._tag_sizes.keys():
                marker._id -= self._marker_offset
                filtered_markers.append(marker)

        return filtered_markers


def init_cameras(webot: WebotsRobot, lock: threading.Lock) -> list[WebotsCameraBoard]:
    camera = maybe_get_robot_device(webot, 'camera', WebotsCamera)
    if camera is None:
        return []
    return [WebotsCameraBoard(webot, camera, lock, MARKER_SIZES)]
