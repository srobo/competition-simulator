from __future__ import annotations

from typing import Callable, Iterable, Sequence, TYPE_CHECKING

from sr.robot3.coordinates.vectors import Vector

from .image import Rectangle
from .tokens import Token
from .convert import WebotsOrientation, rotation_matrix_from_axis_and_angle

if TYPE_CHECKING:
    from controller import CameraRecognitionObject


def build_token_info(
    recognition_object: CameraRecognitionObject,
    size: float,
) -> tuple[Token, Rectangle, CameraRecognitionObject]:
    x, y, z = recognition_object.getPosition()

    token = Token(
        size=size,
        # Webots Z is inverted with regard to the one we want.
        position=Vector((x, y, -z)),
    )
    token.rotate(rotation_matrix_from_axis_and_angle(
        WebotsOrientation(*recognition_object.getOrientation()),
    ))

    return (
        token,
        Rectangle(
            recognition_object.getPositionOnImage(),
            recognition_object.getSizeOnImage(),
        ),
        recognition_object,
    )


def tokens_from_objects(
    objects: Iterable[CameraRecognitionObject],
    get_size: Callable[[CameraRecognitionObject], float],
) -> Sequence[tuple[Token, CameraRecognitionObject]]:
    """
    Constructs tokens from the given recognised objects, ignoring any which are
    judged not to be visible to the camera.
    """

    tokens_with_info = sorted(
        (build_token_info(o, get_size(o)) for o in objects),
        key=lambda x: x[0].position.magnitude(),
    )

    preceding_rectangles: list[Rectangle] = []
    tokens = []
    for token, image_rectangle, recognition_object in tokens_with_info:
        if not any(x.overlaps(image_rectangle) for x in preceding_rectangles):
            tokens.append((token, recognition_object))

        preceding_rectangles.append(image_rectangle)

    return tokens
