from __future__ import annotations

import threading
from math import tan
from typing import Iterable
from pathlib import Path

import cv2
import numpy as np
from controller import Robot as WebotsRobot, Camera as WebotsCamera
from april_vision import (
    Marker,
    Processor,
    __version__ as april_vision_version,
    FrameSource,
)
from numpy.typing import NDArray

from .utils import maybe_get_robot_device

MARKER_SIZES: dict[Iterable[int], int] = {
    range(28): 200,  # 0 - 27 for arena boundary
    range(28, 100): 80,  # Everything else is a token
}


class WebotsCameraSource(FrameSource):
    def __init__(
        self,
        robot: WebotsRobot,
        camera: WebotsCamera,
        lock: threading.Lock,
        fps: int = 30,
    ) -> None:
        self._robot = robot
        self.camera = camera
        self.lock = lock
        self.sample_time = 1000 // fps
        self.image_size = (self.camera.getHeight(), self.camera.getWidth())

    def read(self, fresh: bool = True) -> NDArray[np.uint8]:
        """
        The method for getting a new frame.

        :param fresh: Whether to flush the device's buffer before capturing
        the frame, unused.
        """
        # NOTE while loading from a shaped RGB array makes this code nicer,
        # this is substantially slower. Additionally a reshape is still needed because
        # numpy loads the array with height and width the wrong way around.
        # frame_arr = self.camera.getImageArray()
        # frame_init = np.array(frame_arr, dtype=np.uint8)
        # rgb_frame = frame_init.reshape((frame_init.shape[1], frame_init.shape[0], -1))
        # frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        # A frame is only captured every sample_time milliseconds the camera is enabled
        # so we need to wait for a frame to be captured after loading the frame.
        # We need to maintain the lock while the numpy array is generated as the
        # buffer is freed at the end of the timestep
        self.camera.enable(self.sample_time)
        with self.lock:
            self._robot.step(self.sample_time)

            image_data_raw = self.camera.getImage()
            rgb_frame_raw: NDArray[np.uint8] = np.frombuffer(image_data_raw, np.uint8)

        rgb_frame = rgb_frame_raw.reshape((self.image_size[0], self.image_size[1], 4))
        frame: NDArray[np.uint8] = cv2.cvtColor(rgb_frame, cv2.COLOR_BGRA2BGR)

        self.camera.disable()
        return frame

    def close(self) -> None:
        """Close the underlying capture device."""
        self.camera.disable()


class AprilCameraBoard():
    """
    Virtual Camera Board for detecting fiducial markers.

    Additionally, it will do pose estimation, along with some calibration
    in order to determine the spatial positon and orientation of the markers
    that it has detected.
    """

    name: str = "AprilTag Camera Board"

    def __init__(
        self,
        robot: WebotsRobot,
        camera: WebotsCamera,
        lock: threading.Lock,
        marker_sizes: dict[Iterable[int], int],
        fps: int = 30,
    ):
        self._serial = f"Webots Camera - {camera.getName()}"
        self._marker_offset = 0
        calibration = (
            (camera.getWidth() / 2) / tan(camera.getFov() / 2),  # fx
            (camera.getWidth() / 2) / tan(camera.getFov() / 2),  # fy
            camera.getWidth() // 2,  # cx
            camera.getHeight() // 2,  # cy
        )

        cam = WebotsCameraSource(robot, camera, lock, fps)
        self._camera = Processor(cam, calibration=calibration, name=self._serial)
        self._camera.marker_filter = self._marker_filter
        self._set_marker_sizes(marker_sizes)

    @property
    def serial_number(self) -> str:
        """Get the serial number."""
        return self._serial

    @property
    def firmware_version(self) -> str | None:
        """Get the firmware version of the board."""
        return april_vision_version

    def see(
        self,
        *,
        eager: bool = True,
        frame: NDArray[np.uint8] | None = None,
    ) -> list[Marker]:
        """
        Capture an image and identify fiducial markers.

        :param eager: Process the pose estimations of markers immediately,
            currently unused.
        :returns: list of markers that the camera could see.
        """
        return self._camera.see(frame=frame)

    def see_ids(self, *, frame: NDArray[np.uint8] | None = None) -> list[int]:
        """
        Capture an image and identify fiducial markers.

        This method returns just the marker IDs that are visible.
        :returns: A list of IDs for the markers that were visible.
        """
        return self._camera.see_ids(frame=frame)

    def capture(self) -> NDArray[np.uint8]:
        """
        Get the raw image data from the camera.

        :returns: Camera pixel data
        """
        return self._camera.capture()

    def save(self, path: Path | str, *, frame: NDArray[np.uint8] | None = None) -> None:
        """Save an annotated image to a path."""
        self._camera.save(path, frame=frame)

    def _set_marker_sizes(
        self,
        marker_sizes: dict[Iterable[int], int],
        marker_offset: int = 0,
    ) -> None:
        """Set the sizes of all the markers used in the game."""
        # store marker offset to be used by the filter
        self._marker_offset = marker_offset
        # Reset previously stored sizes
        self._camera.tag_sizes = {}
        for marker_ids, marker_size in marker_sizes.items():
            # Unroll generators to give direct lookup
            for marker_id in marker_ids:
                # Convert to meters
                self._camera.tag_sizes[marker_id + marker_offset] = float(marker_size) / 1000

    def _marker_filter(self, markers: list[Marker]) -> list[Marker]:
        """Apply marker offset and remove markers that are not in the game."""
        filtered_markers: list[Marker] = []
        if not isinstance(self._camera.tag_sizes, dict):
            for marker in markers:
                marker._id -= self._marker_offset
                filtered_markers.append(marker)
            return filtered_markers

        for marker in markers:
            if marker._id in self._camera.tag_sizes.keys():
                marker._id -= self._marker_offset
                filtered_markers.append(marker)

        return filtered_markers


def init_cameras(webot: WebotsRobot, lock: threading.Lock) -> list[AprilCameraBoard]:
    camera = maybe_get_robot_device(webot, 'camera', WebotsCamera)
    if camera is None:
        return []
    return [AprilCameraBoard(webot, camera, lock, MARKER_SIZES)]
