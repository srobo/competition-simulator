from __future__ import annotations

from typing import TypeVar, Iterable, Protocol, Sequence, TYPE_CHECKING

from sr.robot3.coordinates.vectors import Vector

from .image import Rectangle
from .convert import WebotsOrientation, rotation_matrix_from_axis_and_angle
from .markers import FiducialMarker

if TYPE_CHECKING:
    from controller import CameraRecognitionObject as WebotsRecognitionObject


class RecognisedObject(Protocol):
    @property
    def recognition_object(self) -> WebotsRecognitionObject:
        ...

    @property
    def size_m(self) -> float:
        ...


TRecognised = TypeVar('TRecognised', bound=RecognisedObject)


def build_marker_info(
    recognised_object: TRecognised,
) -> tuple[FiducialMarker, Rectangle, TRecognised]:
    recognition_object = recognised_object. recognition_object

    # Webots' axes are different to ours. Account for that in the unpacking
    z, x, y = recognition_object.getPosition()

    marker = FiducialMarker(
        size=recognised_object.size_m,
        # Webots X and Y is inverted with regard to the one we want -- Zoloto
        # has increasing X & Y to the right and down respectively.
        position=Vector((-x, y, z)),
    )
    marker.rotate(rotation_matrix_from_axis_and_angle(
        WebotsOrientation(*recognition_object.getOrientation()),
    ))

    return (
        marker,
        Rectangle(
            recognition_object.getPositionOnImage(),
            recognition_object.getSizeOnImage(),
        ),
        recognised_object,
    )


def markers_from_objects(
    objects: Iterable[TRecognised],
) -> Sequence[tuple[FiducialMarker, TRecognised]]:
    """
    Constructs markers from the given recognised objects, ignoring any which are
    judged not to be visible to the camera.
    """

    markers_with_info = sorted(
        (
            build_marker_info(x)
            for x in objects
        ),
        key=lambda x: x[0].position.magnitude(),
    )

    preceding_rectangles: list[Rectangle] = []
    markers = []
    for marker, image_rectangle, recognised_object in markers_with_info:
        if not any(x.overlaps(image_rectangle) for x in preceding_rectangles):
            markers.append((marker, recognised_object))

        preceding_rectangles.append(image_rectangle)

    return markers
