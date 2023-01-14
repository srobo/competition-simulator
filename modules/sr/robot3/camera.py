from __future__ import annotations

import logging
import threading
from typing import Iterable
from pathlib import Path

from marker import Marker
from controller import Robot as WebotsRobot, Camera as WebotsCamera

from .utils import maybe_get_robot_device

LOGGER = logging.getLogger(__name__)

MARKER_SIZES: dict[Iterable[int], int] = {
    range(28): 200,  # 0 - 27 for arena boundary
    range(28, 100): 80,  # Everything else is a token
}


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
        self._camera.recognitionEnable(self._sample_time)

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
        with self._lock:
            self._capture()
            for recognition_object in self._camera.getRecognitionObjects():
                try:
                    # Get the object's assigned "model" value
                    marker_id = int(recognition_object.getModel())
                except ValueError:
                    LOGGER.warning("Invalid marker id found.")
                    continue

                size = self._tag_sizes.get(marker_id, 0)

                raw_markers.append(Marker(
                    id=marker_id,
                    # X forward, Y left, Z up
                    pose_t=tuple(recognition_object.getPosition()),
                    # In axis-angle form
                    pose_R=tuple(recognition_object.getOrientation()),
                    tag_size=size,
                    pixel_center=tuple(recognition_object.getPositionOnImage()),
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

        with self._lock:
            self._capture()
            self._camera.saveImage(str(path), 100)

    def _capture(self) -> None:
        self._camera.enable(self._sample_time)
        self._robot.step(self._sample_time)
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
