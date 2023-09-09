from __future__ import annotations

import enum
import math
import warnings
from typing import Mapping, Collection, NamedTuple

from sr.robot3.coordinates import vectors
from sr.robot3.coordinates.matrix import Matrix
from sr.robot3.coordinates.vectors import Vector

TOKEN_SIZE = 1

NINETY_DEGREES = math.pi / 2
DEFAULT_ANGLE_TOLERANCE = math.radians(75)


# An orientation object which mimics how Zoloto computes its orientation angles.
class Orientation(NamedTuple):
    rot_x: float
    rot_y: float
    rot_z: float

    @property
    def roll(self) -> float:
        return self.rot_x

    @property
    def pitch(self) -> float:
        return self.rot_y

    @property
    def yaw(self) -> float:
        return self.rot_z

    def yaw_pitch_roll(self) -> tuple[float, float, float]:
        return self.yaw, self.pitch, self.roll


class FaceName(enum.Enum):
    """
    Names of faces on a token in the reference position.

    As a token is rotated, the position of a named face also moves within space.
    That means that the "top" face of a token is not necessarily the one called
    "Top".
    """

    # TODO: rename these in terms of cardinal directions for clarity.  # noqa: T101
    Top = 'top'
    Bottom = 'bottom'

    Left = 'left'
    Right = 'right'

    Front = 'front'
    Rear = 'rear'


class Token:
    """
    Represents a cube which knows its position in space and can be rotated.

    Internally this stores its position in space separately from the positions
    of its corners, which are stored relative to the centre of the cube.

    Tokens have 6 `Face`s, all facing outwards and named for their position on a
    reference cube. Which of these have markers on can optionally be specified
    in the constructor (by default all do).
    """

    def __init__(
        self,
        position: Vector,
        size: float = TOKEN_SIZE,
    ) -> None:
        self.position = position
        self.corners, self.valid_faces = self._init_corners(size)

    def _init_corners(self, size: float) -> tuple[dict[str, Vector], Collection[FaceName]]:
        return (
            {
                'left-top-front': Vector((-1, 1, -1)) * size,
                'right-top-front': Vector((1, 1, -1)) * size,

                'left-bottom-front': Vector((-1, -1, -1)) * size,
                'right-bottom-front': Vector((1, -1, -1)) * size,

                'left-top-rear': Vector((-1, 1, 1)) * size,
                'right-top-rear': Vector((1, 1, 1)) * size,

                'left-bottom-rear': Vector((-1, -1, 1)) * size,
                'right-bottom-rear': Vector((1, -1, 1)) * size,
            },
            FaceName,
        )

    def rotate(self, matrix: Matrix) -> None:
        """
        Rotate the token by the given rotation matrix.
        """
        self.corners = {
            name: matrix * position
            for name, position in self.corners.items()
        }

    def face(self, name: FaceName) -> Face:
        """
        Get the named `Face` of the token.

        As a token is rotated, the position of a named face also moves within
        space. That means that the "top" face of a token is not necessarily the
        one called "Top".
        """
        if name not in self.valid_faces:
            raise ValueError(f"{name} is not a valid face for this token")
        return Face(self, name)

    def corners_global(self) -> dict[str, Vector]:
        """
        A mapping of the corners of the token (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the same origin as used to define the position of the token.
        """
        return {
            name: position + self.position
            for name, position in self.corners.items()
        }

    def visible_faces(self, angle_tolerance: float = DEFAULT_ANGLE_TOLERANCE) -> list[Face]:
        """
        Returns a list of the faces which are visible to the global origin.
        If a token should be considered 2D, only check its front and rear faces.
        """
        faces = [self.face(x) for x in self.valid_faces]
        return [f for f in faces if f.is_visible_to_global_origin(angle_tolerance)]


class FlatToken(Token):
    """
    Represents a 2D fiducial marker which knows its position in space and can be
    rotated.

    Internally this stores its position in space separately from the positions
    of its corners, which are stored relative to the centre of the cuboid that
    represents the marker.

    FlatTokens have one `Face`.

    Instances of this type must have had their proper orientation applied in the
    world file.
    """

    def _init_corners(self, size: float) -> tuple[dict[str, Vector], Collection[FaceName]]:
        # Our wall marker numbering starts on the North wall, so we pick
        # that as our reference markers (and expect them to have zero
        # rotation). Their South face (in our terms) is the one facing into
        # the arena, however as our arena is rotated 90° relative to Webots
        # this ends up as one of the "side"s of the token box.

        # The dimensions here need to end up matching those passed to the marker
        # as defined in `protos/Markers/MarkerBase.proto`, however note that our
        # axes are rotated relative to those in Webots.
        return (
            {
                'right-top-front': Vector((0.0001, size, -size)),
                'right-bottom-front': Vector((0.0001, -size, -size)),

                'right-top-rear': Vector((0.0001, size, size)),
                'right-bottom-rear': Vector((0.0001, -size, size)),
            },
            [FaceName.Right],
        )


class Face:
    """
    Represents a specific named face on a token.

    This is the primary interface to information about an orientated token.
    """

    def __init__(self, token: Token, name: FaceName) -> None:
        self.token = token
        self.name = name

    def __repr__(self) -> str:
        return f'Face({self.token!r}, {self.name!r})'

    def _filter_corners(self, corners: Mapping[str, Vector]) -> dict[str, Vector]:
        return {
            name: position
            for name, position in corners.items()
            if self.name.value in name
        }

    def corners(self) -> dict[str, Vector]:
        """
        A mapping of the corners of the face (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the center of the token.
        """
        return self._filter_corners(self.token.corners)

    def corners_global(self) -> dict[str, Vector]:
        """
        A mapping of the corners of the token (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the same origin as used to define the position of the token.
        """
        return self._filter_corners(self.token.corners_global())

    def normal(self) -> Vector:
        """
        A unit vector expressing the direction normal to the face of the token.
        """
        return vectors.unit_vector(sum(
            self.corners().values(),
            vectors.ZERO_3VECTOR,
        ))

    def centre(self) -> Vector:
        """
        The position of the centre of the face, relative to the token's centre.
        """
        corners = self.corners().values()
        assert len(corners) == 4
        normal = sum(corners, vectors.ZERO_3VECTOR)
        return normal / 4

    def centre_global(self) -> Vector:
        """
        The position of the centre of the face, relative to the origin used for
        the token's position.
        """
        return self.token.position + self.centre()

    def angle_to_global_origin(self) -> float:
        direction_to_origin = -self.centre_global()
        normal = self.normal()
        return vectors.angle_between(direction_to_origin, normal)

    def is_visible_to_global_origin(
        self,
        angle_tolerance: float = DEFAULT_ANGLE_TOLERANCE,
    ) -> bool:
        if angle_tolerance > NINETY_DEGREES:
            raise ValueError(
                "Refusing to allow faces with angles > 90° to be visible "
                "(asked for {} radians, {})".format(
                    angle_tolerance,
                    math.degrees(angle_tolerance),
                ),
            )

        angle_to_origin = self.angle_to_global_origin()
        return abs(angle_to_origin) < angle_tolerance

    def distance(self) -> float:
        """
        The distance to the centre of the face from the origin used for the
        token's position.
        """
        return self.centre_global().magnitude()

    def top_midpoint(self) -> Vector:
        """
        The midpoint of the edge which the apparent marker on this face
        determines to be the "top" edge. It usually doesn't actually matter
        which edge this is, though in some games it does.

        For faces which are not usually vertical, we pick the "rear" of the
        token to equate to be the place to put the "top" edge.
        This also matches how the markers were laid out in "Sunny Side Up".
        """
        if self.name in (FaceName.Top, FaceName.Bottom):
            corners = [
                v for n, v in self.corners().items()
                if FaceName.Rear.value in n
            ]
        else:
            corners = [
                v for n, v in self.corners().items()
                if FaceName.Top.value in n
            ]
        assert len(corners) == 2, "Wrong number of corners for 'top' edge"
        a, b = corners
        return (a + b) / 2

    def orientation(self) -> Orientation:
        # TODO: match this to how Zoloto computes orientation.  # noqa: T101
        warnings.warn(
            "Orientation data in the simulator does not match the robot API. "
            "Either or both may change to resolve this.",
            stacklevel=2,
        )

        n_x, n_y, n_z = self.normal().data

        rot_y = math.atan(n_x / n_z)

        rot_x = math.asin(n_y)

        # Unrotate the normal in X & Y to leave only the Z rotation
        sin_x = math.sin(-rot_x)
        sin_y = math.sin(-rot_y)
        cos_x = math.cos(-rot_x)
        cos_y = math.cos(-rot_y)

        R = Matrix((
            (cos_y, 0, sin_y),
            (-sin_x * -sin_y, cos_x, -sin_x * cos_y),
            (-sin_y * cos_x, sin_x, cos_x * cos_y),
        ))

        unrotated_midpoint = R * self.top_midpoint()

        a_x, a_y, _ = unrotated_midpoint.data
        rot_z = -math.atan2(a_x, a_y)

        return Orientation(-rot_x, rot_y, rot_z)
