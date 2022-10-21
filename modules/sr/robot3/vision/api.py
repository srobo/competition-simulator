from __future__ import annotations

from typing import Callable, Iterable, Sequence, TYPE_CHECKING

import ptvsd
from sr.robot3.coordinates.vectors import Vector

from .image import Rectangle
from .tokens import Token
from .convert import WebotsOrientation, rotation_matrix_from_axis_and_angle

if TYPE_CHECKING:
    from controller import CameraRecognitionObject

ptvsd.enable_attach()


def build_token_info(
    recognition_object: CameraRecognitionObject,
    size: float,
    token_class: type[Token],
) -> tuple[Token, Rectangle, CameraRecognitionObject]:
    # Webots' axes are different to ours. Account for that in the unpacking
    z, x, y = recognition_object.getPosition()

    token = token_class(
        size=size,
        # Webots X and Y is inverted with regard to the one we want -- Zoloto
        # has increasing X & Y to the right and down respectively.
        position=Vector((-x, y, z)),
    )
    w_orient = recognition_object.getOrientation()
    a, b, c, d = w_orient
    print()
    print(f"{a:.4g}, {b:.4g}, {c:.4g}, {d:.4g}")

    # Upright: 0.01625, 0.01641, 0.9997, 1.561
    # roll 90 deg left (counter clockwise): 0.5816, 0.5873, 0.563, 2.108
    # roll 90 deg right (clockwise): -0.5692, -0.5747, 0.588, 2.07
    # upside-down: -0.7036, -0.7105, 0.01144, 3.118

    # Viewed from another position
    # 0.7065, -0.7076, 0.0115, 3.119

    token.rotate(rotation_matrix_from_axis_and_angle(
        WebotsOrientation(*w_orient),
    ))

    for name, vector in token.corners.items():
        print(name, vector)

    print()

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
    get_token_class: Callable[[CameraRecognitionObject], type[Token]],
) -> Sequence[tuple[Token, CameraRecognitionObject]]:
    """
    Constructs tokens from the given recognised objects, ignoring any which are
    judged not to be visible to the camera.
    """

    tokens_with_info = sorted(
        (
            build_token_info(x, get_size(x), get_token_class(x))
            for x in objects
        ),
        key=lambda x: x[0].position.magnitude(),
    )

    preceding_rectangles: list[Rectangle] = []
    tokens = []
    for token, image_rectangle, recognition_object in tokens_with_info:
        if not any(x.overlaps(image_rectangle) for x in preceding_rectangles):
            tokens.append((token, recognition_object))

        preceding_rectangles.append(image_rectangle)

    return tokens
