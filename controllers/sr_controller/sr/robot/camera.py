from sr.robot.settings import TIME_STEP


class Token:
    def __init__(self, recognition_object):
        self._recognition_object = recognition_object

    @property
    def id(self):
        return self._recognition_object.get_id()

    @property
    def position(self):
        return self._recognition_object.get_position()

    @property
    def orientation(self):
        """
        Returns 4 weird values
        """
        return self._recognition_object.get_position()


class Camera:
    def __init__(self, webot):
        self.webot = webot
        self.camera = self.webot.getCamera("camera")
        self.camera.enable(TIME_STEP)
        self.camera.recognitionEnable(TIME_STEP)

    def see(self):
        return [
            Token(recognition_object)
            for recognition_object in self.camera.getRecognitionObjects()
        ]
