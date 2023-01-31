"""
Classes for marker detections and various axis representations.

Setting the environment variable ZOLOTO_LEGACY_AXIS uses the axis that were
used in zoloto<0.9.0. Otherwise the conventional right-handed axis is used
where x is forward, y is left and z is upward.
"""
from __future__ import annotations

import os
from enum import Enum
from math import pi, acos, atan2, hypot
from typing import Dict, List, Tuple, Iterator, NamedTuple

from squaternion import Quaternion


class MarkerType(Enum):
    """
    The available tag families.

    To support Apriltag 2 libraries use tag36h11.
    """

    APRILTAG_16H5 = 'tag16h5'
    APRILTAG_25H9 = 'tag25h9'
    APRILTAG_36H11 = 'tag36h11'
    APRILTAG_21H7 = 'tagCircle21h7'
    APRILTAG_49H12 = 'tagCircle49h12'
    APRILTAG_48H12 = 'tagCustom48h12'
    APRILTAG_41H12 = 'tagStandard41h12'
    APRILTAG_52H13 = 'tagStandard52h13'
    WEBOTS = 'webots'


class PixelCoordinates(NamedTuple):
    """
    Coordinates within an image made up from pixels.

    Floating point type is used to allow for subpixel detected locations
    to be represented.

    :param float x: X coordinate
    :param float y: Y coordinate
    """

    x: float
    y: float


class CartesianCoordinates(NamedTuple):
    """
    A 3 dimensional cartesian coordinate in the standard right-handed cartesian system.

    Origin is at the camera.

    The X axis extends directly away from the camera. Zero is at the camera.
    Increasing values indicate greater distance from the camera.

    The Y axis is horizontal relative to the camera's perspective, i.e: right
    to left within the frame of the image. Zero is at the centre of the image.
    Increasing values indicate greater distance to the left.

    The Z axis is vertical relative to the camera's perspective, i.e: down to
    up within the frame of the image. Zero is at the centre of the image.
    Increasing values indicate greater distance above the centre of the image.

    More information: https://w.wiki/5zbE

    Legacy:
    The X axis is horizontal relative to the camera's perspective, i.e: left &
    right within the frame of the image. Zero is at the centre of the image.
    Increasing values indicate greater distance to the right.

    The Y axis is vertical relative to the camera's perspective, i.e: up & down
    within the frame of the image. Zero is at the centre of the image.
    Increasing values indicate greater distance below the centre of the image.

    The Z axis extends directly away from the camera. Zero is at the camera.
    Increasing values indicate greater distance from the camera.

    These match traditional cartesian coordinates when the camera is facing
    upwards.


    :param float x: X coordinate, in millimeters
    :param float y: Y coordinate, in millimeters
    :param float z: Z coordinate, in millimeters
    """

    x: float
    y: float
    z: float

    @classmethod
    def from_tvec(cls, x: float, y: float, z: float) -> CartesianCoordinates:
        """
        Convert coordinate system to standard right-handed cartesian system.

        The pose estimation coordinate system has the origin at the camera center.
        Also converts units to millimeters.

        :param float x: The x-axis points from the camera center out the camera lens.
        :param float y: The y-axis is to the left in the image taken by the camera.
        :param float z: The z-axis is up in the image taken by the camera.
        """
        if os.environ.get('ZOLOTO_LEGACY_AXIS'):
            return cls(x=-y * 1000, y=-z * 1000, z=x * 1000)
        else:
            return cls(x=x * 1000, y=y * 1000, z=z * 1000)


class SphericalCoordinate(NamedTuple):
    """
    A 3 dimensional spherical coordinate location.

    The conventional spherical coordinate in mathematical notation where θ is
    a rotation around the vertical axis and φ is measured as the angle from
    the vertical axis.
    More information: https://mathworld.wolfram.com/SphericalCoordinates.html

    :param float distance: Radial distance from the origin, in millimeters.
    :param float theta: Azimuth angle, θ, in radians. This is the angle from
        directly in front of the camera to the vector which points to the
        location in the horizontal plane. A positive value indicates a
        counter-clockwise rotation. Zero is at the centre of the image.
    :param float phi: Polar angle, φ, in radians. This is the angle "down"
        from the vertical axis to the vector which points to the location.
        Zero is directly upward.
    """

    distance: int
    theta: float
    phi: float

    @property
    def rot_x(self) -> float:
        """
        Rotation around the x-axis.

        Conventional:  This is unused.
        Legacy: A rotation up to down around the camera, in radians. Values
                increase as the marker moves towards the bottom of the image.
                A zero value is halfway up the image.
        """
        if os.environ.get('ZOLOTO_LEGACY_AXIS'):
            return self.phi - (pi / 2)
        else:
            raise AttributeError(
                "That axis is not available in the selected coordinate system.")

    @property
    def rot_y(self) -> float:
        """
        Rotation around the y-axis.

        Conventional: A rotation up to down around the camera, in radians.
                      Values increase as the marker moves towards the bottom
                      of the image. A zero value is halfway up the image.
        Legacy: A rotation left to right around the camera, in radians. Values
                increase as the marker moves towards the right of the image.
                A zero value is on the centerline of the image.
        """
        if os.environ.get('ZOLOTO_LEGACY_AXIS'):
            return -self.theta
        else:
            return self.phi - (pi / 2)

    @property
    def rot_z(self) -> float:
        """
        Rotation around the z-axis.

        Conventional: A rotation right to left around the camera, in radians.
                      Values increase as the marker moves towards the left of
                      the image. A zero value is on the centerline of the
                      image.
        Legacy: This is unused.
        """
        if os.environ.get('ZOLOTO_LEGACY_AXIS'):
            raise AttributeError(
                "That axis is not available in the selected coordinate system.")
        else:
            return self.theta

    @classmethod
    def from_tvec(cls, x: float, y: float, z: float) -> SphericalCoordinate:
        """
        Convert coordinate system to standard right-handed cartesian system.

        The pose estimation coordinate system has the origin at the camera center.

        :param float x: The x-axis points from the camera center out the camera lens.
        :param float y: The y-axis is to the left in the image taken by the camera.
        :param float z: The z-axis is up in the image taken by the camera.
        """
        dist = hypot(x, y, z)
        theta = atan2(y, x)
        phi = acos(z / dist)
        return cls(int(dist * 1000), theta, phi)


ThreeTuple = Tuple[float, float, float]
RotationMatrix = Tuple[ThreeTuple, ThreeTuple, ThreeTuple]


class Orientation:
    """The orientation of an object in 3-D space."""

    __ZOLOTO_LEGACY_ORIENTATION = Quaternion.from_angle_axis(
        angle=pi, axis=(1, 0, 0),
    )

    def __init__(self, rotation_matrix: tuple[float, float, float, float]):
        """
        Construct a quaternion given the rotation matrix in the camera's coordinate system.

        More information:
        https://en.wikipedia.org/wiki/Rotation_matrix#In_three_dimensions
        """
        x, y, z, rad = rotation_matrix
        # Calculate the quaternion of the rotation in the camera's coordinate system
        # Correct for roll and yaw turning the wrong way
        quaternion = Quaternion.from_angle_axis(angle=rad, axis=(-x, y, -z))

        self.__rotation_matrix: RotationMatrix = quaternion.to_rot()

        if os.environ.get('ZOLOTO_LEGACY_AXIS'):
            # Remap axis for zoloto's axis () and adjust pitch zero position
            self._quaternion = Quaternion(
                w=quaternion.w, x=-quaternion.y, y=quaternion.z, z=-quaternion.x,
            ) * self.__ZOLOTO_LEGACY_ORIENTATION
        else:
            self._quaternion = quaternion

        roll, pitch, yaw = quaternion.to_euler()

        self._yaw_pitch_roll: ThreeTuple = yaw, pitch, roll

    @property
    def rot_x(self) -> float:
        """
        Get rotation angle around X axis in radians.

        The roll rotation with zero as the April Tags marker reference point
        at the top left of the marker.

        Legacy: The inverted pitch rotation with zero as the marker facing
                directly away from the camera and a positive rotation being
                downward.
                The practical effect of this is that an April Tags marker
                facing the camera square-on will have a value of ``pi`` (or
                equivalently ``-pi``).
        """
        return self.yaw_pitch_roll[2]

    @property
    def rot_y(self) -> float:
        """
        Get rotation angle around Y axis in radians.

        The pitch rotation with zero as the marker facing the camera square-on
        and a positive rotation being upward.

        Legacy: The inverted yaw rotation with zero as the marker facing the
                camera square-on and a positive rotation being
                counter-clockwise.
        """
        return self.yaw_pitch_roll[1]

    @property
    def rot_z(self) -> float:
        """
        Get rotation angle around Z axis in radians.

        The yaw rotation with zero as the marker facing the camera square-on
        and a positive rotation being clockwise.

        Legacy: The roll rotation with zero as the marker facing the camera
                square-on and a positive rotation being clockwise.
        """
        return self.yaw_pitch_roll[0]

    @property
    def yaw(self) -> float:
        """
        Get yaw of the marker, a rotation about the vertical axis, in radians.

        Positive values indicate a rotation clockwise from the perspective of
        the marker.

        Zero values have the marker facing the camera square-on.
        """
        return self._yaw_pitch_roll[0]

    @property
    def pitch(self) -> float:
        """
        Get pitch of the marker, a rotation about the transverse axis, in radians.

        Positive values indicate a rotation upwards from the perspective of the
        marker.

        Zero values have the marker facing the camera square-on.
        """
        return self._yaw_pitch_roll[1]

    @property
    def roll(self) -> float:
        """
        Get roll of the marker, a rotation about the longitudinal axis, in radians.

        Positive values indicate a rotation clockwise from the perspective of
        the marker.

        Zero values have the marker facing the camera square-on.
        """
        return self._yaw_pitch_roll[2]

    @property
    def yaw_pitch_roll(self) -> ThreeTuple:
        """
        Get the equivalent yaw-pitch-roll angles.

        Specifically intrinsic Tait-Bryan angles following the z-y'-x'' convention.
        """
        roll, pitch, yaw = self._quaternion.to_euler()
        return yaw, pitch, roll

    def __iter__(self) -> Iterator[float]:
        """
        Get an iterator over the rotation angles.
        Returns:
            An iterator of floating point angles in order x, y, z.
        """
        return iter([self.rot_x, self.rot_y, self.rot_z])

    @property
    def rotation_matrix(self) -> RotationMatrix:
        """
        Get the rotation matrix represented by this orientation.

        Returns:
            A 3x3 rotation matrix as a tuple of tuples.
        """
        return self.__rotation_matrix

    @property
    def quaternion(self) -> tuple[float, float, float, float]:
        """Get the quaternion represented by this orientation."""
        quaternion: tuple[float, float, float, float] = self._quaternion.to_tuple()
        return quaternion

    def __repr__(self) -> str:
        return "Orientation(rot_x={}, rot_y={}, rot_z={})".format(
            self.rot_x, self.rot_y, self.rot_z,
        )


class Marker:
    """Wrapper of a marker detection with axis and rotation calculated."""

    def __init__(
        self,
        id: int,  # noqa: A002
        pose_t: tuple[float, float, float],
        # In axis-angle form
        pose_R: tuple[float, float, float, float],
        tag_size: float,
        pixel_center: tuple[int, int],
        pixel_corners: list[tuple[int, int]],
    ):
        self.__marker_type = MarkerType.WEBOTS
        self._id = id
        self.__pixel_center = PixelCoordinates(*pixel_center)
        self.__pixel_corners = [PixelCoordinates(x, y) for x, y in pixel_corners]
        self.__size = int(tag_size * 1000)
        self._tvec = pose_t
        self._rvec = pose_R

        self.__distance = int(hypot(*self._tvec) * 1000)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} size={self.size} "
            f"type={self.marker_type.name} distance={self.distance}>")

    @property  # noqa: A003
    def id(self) -> int:  # noqa: A003
        """The marker id number."""
        return self._id

    @property
    def size(self) -> int:
        """The size of the detected marker in millimeters."""
        return self.__size

    @property
    def marker_type(self) -> MarkerType:
        """The family of the detected marker, likely tag36h11."""
        return self.__marker_type

    @property
    def pixel_corners(self) -> List[PixelCoordinates]:
        """The pixels of the corners of the marker in the image."""
        return self.__pixel_corners

    @property
    def pixel_centre(self) -> PixelCoordinates:
        """The pixel location of the center of the marker in the image."""
        return self.__pixel_center

    @property
    def distance(self) -> int:
        """The distance between the marker and camera, in millimeters."""
        return self.__distance

    @property
    def orientation(self) -> Orientation:
        """The marker's orientation."""
        if self._rvec is not None:
            return Orientation(self._rvec)
        raise RuntimeError("This marker was detected with an uncalibrated camera")

    @property
    def spherical(self) -> SphericalCoordinate:
        """The spherical coordinates of the marker's location relative to the camera."""
        if self._tvec is not None:
            return SphericalCoordinate.from_tvec(*self._tvec)
        raise RuntimeError("This marker was detected with an uncalibrated camera")

    @property
    def cartesian(self) -> CartesianCoordinates:
        """The cartesian coordinates of the marker's location relative to the camera."""
        if self._tvec is not None:
            return CartesianCoordinates.from_tvec(*self._tvec)
        raise RuntimeError("This marker was detected with an uncalibrated camera")

    def as_dict(self) -> Dict[str, int | float | PixelCoordinates | list[float]]:
        """The marker data as a dict."""
        marker_dict: Dict[str, int | float | PixelCoordinates | list[float]] = {
            "id": self._id,
            "size": self.__size,
            "pixel_center": self.__pixel_center,
        }
        if self._tvec is not None and self._rvec is not None:
            marker_dict.update(
                {"rvec": list(self._rvec), "tvec": list(self._tvec)},
            )
        return marker_dict
