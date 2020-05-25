import vectors
from tokens import Token, FaceName
from webots import CameraRecognitionObject
from convert import WebotsOrientation, rotation_matrix_from_axis_and_angle
from vectors import Vector

webots_camera_recognition_object = NotImplemented  # type: CameraRecognitionObject

TOKEN_SIZE = 42 # TODO?

# TODO: use `webots_camera_recognition_object.get_position_on_image` and
# `webots_camera_recognition_object.get_size_on_image` to determine whether the
# object can actually be seen.

token = Token(
    position=Vector(webots_camera_recognition_object.get_position()),
    size=TOKEN_SIZE,
)
token.rotate(rotation_matrix_from_axis_and_angle(WebotsOrientation(
    *webots_camera_recognition_object.get_orientation(),
)))

for face_name in FaceName:
    face = token.face(face_name)

    direction_to_face = face.centre_global()
    direction_face_is_facing = face.normal()

    angle_between = vectors.angle_between(
        direction_to_face,
        # Negate so that faces which are facing the camera have small angles,
        # making our comparisons easier to reason about).
        -direction_face_is_facing,
    )

    if abs(angle_between) > 75:
        # Camreas can't see faces at oblique angles (this also excludes things
        # facing away from the camera).
        continue

    orientation = face.orientation()
    print(orientation)
