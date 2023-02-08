"""
This file converts from local-space coördinates of four corners of a detected
marker, and converts them to an Orientation object.

This is implemented in pure Python for portability.
"""

from __future__ import annotations

import math
import enum
import dataclasses

class LocalCoordinateSystem(enum.Enum):
    """
    What form of coördinates are we using?"
    """

    # NED: +x is forward, +y is right, +z is down
    # This is the 'standard' coördinate system; we implement it here as
    # per Janota et al 2015. It is widely used in aviation and has the
    # best sources on conversion to Tait-Bryan angles.
    NED = 0

    # Graphics/OpenGL: +x is right, +y is up, +z is forward
    GRAPHICS_OPENGL = 1
    # This is also the 'conventional' SR coördinate system

    # Graphics/Direct3D: +x is right, +y is down, +z is backward
    GRAPHICS_DIRECT3D = 2

    # Computer vision: +x is right, +y is down, +z is forward
    VISION = 3
    # Zoloto follows this convention

    # East-North-Up: +x is forward, +y is left, +z is up
    ENU = 4
    # Both Webots and ROS use this convention

    # Maritime science: +x is forward, +y is right, +z is up
    MARITIME = 5


_IS_RIGHT_HANDED = {
    LocalCoordinateSystem.NED,
    LocalCoordinateSystem.VISION,
    LocalCoordinateSystem.ENU,
}


Vector3 = tuple[float, float, float]


def _to_ned(vector: Vector3, system: LocalCoordinateSystem) -> Vector3:
    """
    Convert a vector from the given coördinate system to NED coördinates.
    """
    if system == LocalCoordinateSystem.NED:
        return vector

    if system == LocalCoordinateSystem.GRAPHICS_OPENGL:
        return (vector[2], vector[0], -vector[1])
    elif system == LocalCoordinateSystem.GRAPHICS_DIRECT3D:
        return (-vector[2], vector[0], vector[1])
    elif system == LocalCoordinateSystem.VISION:
        return (vector[2], vector[0], vector[1])
    elif system == LocalCoordinateSystem.ENU:
        return (vector[0], -vector[1], -vector[2])
    elif system == LocalCoordinateSystem.MARITIME:
        return (vector[0], vector[1], -vector[2])

    raise ValueError(f"Unknown coördinate system {system}")


def _from_ned(vector: Vector3, system: LocalCoordinateSystem) -> Vector3:
    """
    Convert a vector from NED coördinates to the given coördinate system.
    """
    if system == LocalCoordinateSystem.NED:
        return vector

    if system == LocalCoordinateSystem.GRAPHICS_OPENGL:
        return (vector[1], -vector[2], vector[0])
    elif system == LocalCoordinateSystem.GRAPHICS_DIRECT3D:
        return (vector[1], vector[2], -vector[0])
    elif system == LocalCoordinateSystem.VISION:
        return (vector[1], vector[2], vector[0])
    elif system == LocalCoordinateSystem.ENU:
        return (vector[0], -vector[1], -vector[2])
    elif system == LocalCoordinateSystem.MARITIME:
        return (vector[0], vector[1], -vector[2])

    raise ValueError(f"Unknown coördinate system {system}")


def convert_coordinates(
    vector: Vector3,
    from_system: LocalCoordinateSystem,
    to_system: LocalCoordinateSystem,
) -> Vector3:
    """
    Convert a vector from one coördinate system to another.
    """
    return _from_ned(_to_ned(vector, from_system), to_system)


# Some vector utilities
def _vector_add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vector_sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vector_length(vector: Vector3) -> float:
    return math.hypot(vector[0], vector[1], vector[2])


def _vector_normalize(vector: Vector3) -> Vector3:
    length = _vector_length(vector)
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def _vector_dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vector_cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )



def _compute_rotation_matrix(
    *,
    top_left: Vector3,
    top_right: Vector3,
    bottom_left: Vector3,
    bottom_right: Vector3,
) -> tuple[Vector3, Vector3, Vector3]:
    # Compute the tangent and bitangent vectors, which represent our
    # "rotated" Y and Z axes
    rotated_y = _vector_normalize(_vector_sub(top_left, top_right))
    rotated_z = _vector_normalize(_vector_sub(bottom_right, top_right))

    # Compute the normal vector, which represents our "rotated" X axis
    rotated_x = _vector_normalize(_vector_cross(rotated_y, rotated_z))

    # For numerical stability, we need to be very sure the vectors really
    # are orthogonal. For this we take the classic CG trick of recomputing the
    # bitangent (the Z axis) from the cross product of the tangent and normal.
    rotated_z = _vector_normalize(_vector_cross(rotated_x, rotated_y))

    # The rotation matrix is the columns of the new basis vectors.
    # We transpose it to get the rows, which is what we want.
    return [
        [rotated_x[0], rotated_y[0], rotated_z[0]],
        [rotated_x[1], rotated_y[1], rotated_z[1]],
        [rotated_x[2], rotated_y[2], rotated_z[2]],
    ]


# We only use 4-tuples as quaternions; other code uses the `squaternion`
# library, but the conversion is trivial and this avoids an extra dependency.
# Besides which, squaternion is a bit of a mess, and it would be better to
# move away from it to something like scipy.spatial.transform.
RawQuaternion = tuple[float, float, float, float]


def _convert_rotation_matrix_to_quaternion(
    rotation_matrix: tuple[Vector3, Vector3, Vector3],
) -> RawQuaternion:
    # Rotation to quaternion algorithm per Day 2015

    m00, m01, m02 = rotation_matrix[0]
    m10, m11, m12 = rotation_matrix[1]
    m20, m21, m22 = rotation_matrix[2]

    if m22 < 0:
        if m00 > m11:
            t = 1 + m00 - m11 - m22
            q = (
                t,
                m01 + m10,
                m20 + m02,
                m21 - m12,
            )
        else:
            t = 1 - m00 + m11 - m22
            q = (
                m01 + m10,
                t,
                m12 + m21,
                m02 - m20,
            )
    else:
        if m00 < -m11:
            t = 1 - m00 - m11 + m22
            q = (
                m20 + m02,
                m12 + m21,
                t,
                m10 - m01,
            )
        else:
            t = 1 + m00 + m11 + m22
            q = (
                m12 - m21,
                m20 - m02,
                m01 - m10,
                t,
            )

    factor = 0.5 / math.sqrt(t)

    return [
        x * factor
        for x in q
    ]


@dataclasses.dataclass(frozen=True)
class Orientation:
    angle: float
    axis: Vector3
    quaternion: RawQuaternion


def _compute_orientation_from_quaternion(
    quaternion: RawQuaternion,
) -> Orientation:
    w, x, y, z = quaternion

    # Compute the angle
    angle = 2 * math.acos(w)

    # Compute the axis
    factor = 1 / math.sqrt(1 - w * w)
    axis = (
        x * factor,
        y * factor,
        z * factor,
    )

    return Orientation(
        angle=angle,
        axis=axis,
        quaternion=quaternion,
    )


def convert_orientation(
    orientation: Orientation,
    from_system: LocalCoordinateSystem,
    to_system: LocalCoordinateSystem,
) -> Orientation:
    invert_angle = (
        from_system in _IS_RIGHT_HANDED
    ) ^ (
        to_system in _IS_RIGHT_HANDED
    )

    return Orientation(
        angle=-orientation.angle if invert_angle else orientation.angle,
        axis=convert_coordinates(
            orientation.axis,
            from_system=from_system,
            to_system=to_system,
        ),
        quaternion=tuple([
            orientation.quaternion[0],
            *convert_coordinates(
                orientation.quaternion[1:],
                from_system=from_system,
                to_system=to_system,
            ),
        ]),
    )


def _invert_y(vector: Vector3) -> Vector3:
    return (
        vector[0],
        -vector[1],
        vector[2],
    )


def compute_orientation(
    *,
    top_left: Vector3,
    top_right: Vector3,
    bottom_left: Vector3,
    bottom_right: Vector3,
    coordinate_system: LocalCoordinateSystem,
    output_coordinate_system: LocalCoordinateSystem | None = None,
) -> Orientation:
    """
    Compute the orientation of a rectangle in 3D space.

    The rectangle is defined by four points, and we give the orientation relative
    to the vector pointing opposite the camera's direction. This means that a yaw
    of 0 represents the rectangle 'facing' the camera.
    """

    top_left_ned = convert_coordinates(top_left, coordinate_system, LocalCoordinateSystem.NED)
    top_right_ned = convert_coordinates(top_right, coordinate_system, LocalCoordinateSystem.NED)
    bottom_left_ned = convert_coordinates(bottom_left, coordinate_system, LocalCoordinateSystem.NED)
    bottom_right_ned = convert_coordinates(bottom_right, coordinate_system, LocalCoordinateSystem.NED)

    # Since our reference orientation has the marker _facing_ the camera, rather
    # than co-oriented with the camera, we need to flip the y (east) axis.
    top_left_ned = _invert_y(top_left_ned)
    top_right_ned = _invert_y(top_right_ned)
    bottom_left_ned = _invert_y(bottom_left_ned)
    bottom_right_ned = _invert_y(bottom_right_ned)

    rotation_matrix = _compute_rotation_matrix(
        top_left=top_left_ned,
        top_right=top_right_ned,
        bottom_left=bottom_left_ned,
        bottom_right=bottom_right_ned,
    )

    quaternion = _convert_rotation_matrix_to_quaternion(rotation_matrix)

    orientation_ned = _compute_orientation_from_quaternion(quaternion)

    if output_coordinate_system is None:
        output_coordinate_system = coordinate_system

    return convert_orientation(
        orientation_ned,
        from_system=LocalCoordinateSystem.NED,
        to_system=output_coordinate_system,
    )


if __name__ == '__main__':
    import random
    import tqdm

    for _ in tqdm.trange(1_000_000):
        from_system = random.choice(list(LocalCoordinateSystem))
        to_system = random.choice(list(LocalCoordinateSystem))
        x = random.uniform(-100, 100)
        y = random.uniform(-100, 100)
        z = random.uniform(-100, 100)
        vector = (x, y, z)
        intermediate = convert_coordinates(vector, from_system, to_system)
        back_again = convert_coordinates(intermediate, to_system, from_system)
        assert math.isclose(back_again[0], vector[0])
        assert math.isclose(back_again[1], vector[1])
        assert math.isclose(back_again[2], vector[2])
