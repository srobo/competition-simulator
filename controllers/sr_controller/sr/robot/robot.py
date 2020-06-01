import time
from threading import Thread

from sr.robot import motor, camera, ruggeduino
from sr.robot.game import stop_after_delay
from sr.robot.settings import TIME_STEP

# Webots specific library
from controller import Robot as WebotsRobot  # type: ignore[import] # isort:skip


class Robot(object):
    """Class for initialising and accessing robot hardware"""

    def __init__(self, quiet=False, init=True):
        self._initialised = False
        self._quiet = quiet

        # TODO set these values dynamically
        self.mode = "dev"
        self.zone = 0
        self.arena = "A"

        self.__webot = WebotsRobot()

        if init:
            self._init()
            self.wait_start()
            if self.mode == "comp":
                stop_after_delay()

    @classmethod
    def setup(cls):
        return cls()

    def _init(self):
        self.__webots_init()
        self._init_devs()
        self._initialised = True

    def __webots_init(self):
        t = Thread(target=self.__webot_run_robot)
        t.start()
        time.sleep(TIME_STEP / 1000)

    def __webot_run_robot(self):
        while not self.__webot.step(TIME_STEP):
            pass

    def wait_start(self):
        "Wait for the start signal to happen"

        if self.mode not in ["comp", "dev"]:
            raise Exception(
                "mode of '%s' is not supported -- must be 'comp' or 'dev'" % self.mode,
            )
        if self.zone < 0 or self.zone > 3:
            raise Exception(
                "zone must be in range 0-3 inclusive -- value of %i is invalid" % self.zone,
            )
        if self.arena not in ["A", "B"]:
            raise Exception("arena must be A or B")

    def _init_devs(self):
        "Initialise the attributes for accessing devices"

        # Motor boards
        self._init_motors()

        # Ruggeduinos
        self._init_ruggeduinos()

        # Camera
        self._init_camera()

    def _init_motors(self):
        self.motors = motor.init_motor_array(self.__webot)

    def _init_ruggeduinos(self):
        self.ruggeduinos = ruggeduino.init_ruggeduino_array(self.__webot)

    def _init_camera(self):
        self.camera = camera.Camera(self.__webot)
        self.see = self.camera.see
