from sr.robot import motor
from controller import Robot as WebotsRobot # Webots specific library
from threading import Thread
import time
import sys

# Webots constants
TIME_STEP = 64
MAX_SPEED = 12.3

class Robot(object):
    """Class for initialising and accessing robot hardware"""

    def __init__( self,
                  quiet = False,
                  init = True):

        # Check this is the right version of Python before continuing
        assert sys.version_info >= (2, 7) and sys.version_info < (3, 0)

        self._initialised = False
        self._quiet = quiet

        # TODO set these values dynamically
        self.mode = "comp"
        self.zone = 0
        self.arena = "A"

        self.webot = WebotsRobot()

        if init:
            self.init()
            self.wait_start()

    @classmethod
    def setup(cls):
        return cls()

    def init(self):
        self.webots_init()
        self._init_devs()
        self._initialised = True

    def webots_init(self):
        t = Thread(target=self.webot_run_robot)
        t.start()
        time.sleep(TIME_STEP / 1000)

    def webot_run_robot(self):
        while not self.webot.step(TIME_STEP):
            pass

    def wait_start(self):
        "Wait for the start signal to happen"

        if self.mode not in ["comp", "dev"]:
            raise Exception( "mode of '%s' is not supported -- must be 'comp' or 'dev'" % self.mode )
        if self.zone < 0 or self.zone > 3:
            raise Exception( "zone must be in range 0-3 inclusive -- value of %i is invalid" % self.zone )
        if self.arena not in ["A", "B"]:
            raise Exception( "arena must be A or B")

    def _init_devs(self):
        "Initialise the attributes for accessing devices"

        # Motor boards
        self._init_motors()

    def _init_motors(self):
        self.motors = motor.init_motor_array(self.webot)

