from typing import Sequence

import api
from webots import CameraRecognitionObject

webots_camera_recognition_objects = NotImplemented  # type: Sequence[CameraRecognitionObject]

for token in api.tokens_from_objects(webots_camera_recognition_objects):
    for face in token.visible_faces():
        orientation = face.orientation()
        print(orientation)
