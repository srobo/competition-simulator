from tokens import Token
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

for face in token.visible_faces():
    orientation = face.orientation()
    print(orientation)
