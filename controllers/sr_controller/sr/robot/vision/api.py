from typing import List, Tuple, Callable, Iterable, Sequence, TYPE_CHECKING

from .image import Rectangle
from .tokens import Token
from .convert import WebotsOrientation, rotation_matrix_from_axis_and_angle
from .vectors import Vector

if TYPE_CHECKING:
    from controller import CameraRecognitionObject


def build_token_info(
    recognition_object: 'CameraRecognitionObject',
    size: float,
) -> Tuple[Token, Rectangle, 'CameraRecognitionObject']:
    x, y, z = recognition_object.get_position()

    token = Token(
        size=size,
        # Webots Z is inverted with regard to the one we want.
        position=Vector((x, y, -z)),
    )
    token.rotate(rotation_matrix_from_axis_and_angle(
        WebotsOrientation(*recognition_object.get_orientation()),
    ))

    return (
        token,
        Rectangle(
            recognition_object.get_position_on_image(),
            recognition_object.get_size_on_image(),
        ),
        recognition_object,
    )


def tokens_from_objects(
    objects: 'Iterable[CameraRecognitionObject]',
    get_size: 'Callable[[CameraRecognitionObject], float]',
) -> Sequence[Tuple[Token, 'CameraRecognitionObject']]:
    """
    Constructs tokens from the given recognised objects, ignoring any which are
    judged not to be visible to the camera.
    """

    tokens_with_info = sorted(
        (build_token_info(o, get_size(o)) for o in objects),
        key=lambda x: x[0].position.magnitude(),
    )

    preceding_rectangles = []  # type: List[Rectangle]
    tokens = []
    for token, image_rectangle, recognition_object in tokens_with_info:
        if not any(x.overlaps(image_rectangle) for x in preceding_rectangles):
            tokens.append((token, recognition_object))

        preceding_rectangles.append(image_rectangle)

    return tokens
