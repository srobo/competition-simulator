from typing import List, Tuple, Sequence, TYPE_CHECKING

from .image import Rectangle
from .tokens import Token
from .convert import WebotsOrientation, rotation_matrix_from_axis_and_angle
from .vectors import Vector

if TYPE_CHECKING:
    from .webots import CameraRecognitionObject


def build_token_and_rectangle(
    recognition_object: 'CameraRecognitionObject',
) -> Tuple[Token, Rectangle]:
    token = Token(position=Vector(recognition_object.get_position()))
    token.rotate(rotation_matrix_from_axis_and_angle(
        WebotsOrientation(*recognition_object.get_orientation()),
    ))

    return (
        token,
        Rectangle(
            recognition_object.get_position_on_image(),
            recognition_object.get_size_on_image(),
        ),
    )


def tokens_from_objects(objects: 'Sequence[CameraRecognitionObject]') -> Sequence[Token]:
    """
    Constructs tokens from the given recognised objects, ignoring any which are
    judged not to be visible to the camera.
    """

    # TODO: filter out non-tokens

    tokens_with_image_rectangles = sorted(
        (build_token_and_rectangle(o) for o in objects),
        key=lambda x: x[0].position.magnitude(),
    )

    preceding_rectangles = []  # type: List[Rectangle]
    tokens = []
    for token, image_rectangle in tokens_with_image_rectangles:
        if not any(x.overlaps(image_rectangle) for x in preceding_rectangles):
            tokens.append(token)

        preceding_rectangles.append(image_rectangle)

    return tokens
