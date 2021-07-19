import enum
import math
from typing import Dict, List, Mapping, NamedTuple

from sr.robot.coordinates import vectors
from sr.robot.coordinates.matrix import Matrix
from sr.robot.coordinates.vectors import Vector

TOKEN_SIZE = 1


# An orientation object which mimicks how libkoki computes its orientation angles.
Orientation = NamedTuple('Orientation', (
    ('rot_x', float),
    ('rot_y', float),
    ('rot_z', float),
))


class FaceName(enum.Enum):
    """
    Names of faces on a token in the reference position.

    As a token is rotated, the position of a named face also moves within space.
    That means that the "top" face of a token is not neccesarily the one called
    "Top".
    """

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
    reference cube.
    """

    def __init__(self, position: Vector, size: float = TOKEN_SIZE) -> None:
        self.position = position
        self.corners = {
            'left-top-front': Vector((-1, 1, -1)) * size,
            'right-top-front': Vector((1, 1, -1)) * size,

            'left-bottom-front': Vector((-1, -1, -1)) * size,
            'right-bottom-front': Vector((1, -1, -1)) * size,

            'left-top-rear': Vector((-1, 1, 1)) * size,
            'right-top-rear': Vector((1, 1, 1)) * size,

            'left-bottom-rear': Vector((-1, -1, 1)) * size,
            'right-bottom-rear': Vector((1, -1, 1)) * size,
        }

    def rotate(self, matrix: Matrix) -> None:
        """
        Rotate the token by the given rotation matrix.
        """
        self.corners = {
            name: matrix * position
            for name, position in self.corners.items()
        }

    def face(self, name: FaceName) -> 'Face':
        """
        Get the named `Face` of the token.

        As a token is rotated, the position of a named face also moves within
        space. That means that the "top" face of a token is not neccesarily the
        one called "Top".
        """
        return Face(self, name)

    def corners_global(self) -> Dict[str, Vector]:
        """
        A mapping of the corners of the token (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the same origin as used to define the position of the token.
        """
        return {
            name: position + self.position
            for name, position in self.corners.items()
        }

    def visible_faces(self, angle_tolernace: float = 75, is_2d: bool = False) -> 'List[Face]':
        """
        Returns a list of the faces which are visible to the global origin.
        If a token should be considered 2D, only check its front and rear faces.
        """
        face_names = [FaceName.Front, FaceName.Rear] if is_2d else list(FaceName)
        faces = [self.face(x) for x in face_names]
        return [f for f in faces if f.is_visible_to_global_origin(angle_tolernace)]


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

    def _filter_corners(self, corners: Mapping[str, Vector]) -> Dict[str, Vector]:
        return {
            name: position
            for name, position in corners.items()
            if self.name.value in name
        }

    def corners(self) -> Dict[str, Vector]:
        """
        A mapping of the corners of the face (named for their apparent position
        on a reference token) to the current position of that corner relative to
        the center of the token.
        """
        return self._filter_corners(self.token.corners)

    def corners_global(self) -> Dict[str, Vector]:
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

    def is_visible_to_global_origin(self, angle_tolernace: float = 75) -> bool:
        if angle_tolernace > 90:
            raise ValueError(
                "Refusing to allow faces with angles > 90 to be visible "
                f"(asked for {angle_tolernace})",
            )

        direction_to_origin = -self.centre_global()
        normal = self.normal()

        angle_to_origin = vectors.angle_between(direction_to_origin, normal)

        return abs(angle_to_origin) < angle_tolernace

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
        This also matches how the markes were laid out in "Sunny Side Up".
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

        return Orientation(
            math.degrees(-rot_x),
            math.degrees(rot_y),
            math.degrees(rot_z),
        )
