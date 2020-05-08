from sr import motor
from controller import Robot as WebotsRobot # Webots specific library
from threading import Thread
import time

# Webots constants
TIME_STEP = 64
MAX_SPEED = 12.3

class AlreadyInitialised(Exception):
    "The robot has been initialised twice"
    def __str__(self):
        return "Robot object can only be initialised once."

class UnavailableAfterInit(Exception):
    "The called function is unavailable after init()"
    def __str__(self):
        return "The called function is unavailable after init()"

def pre_init(f):
    "Decorator for functions that may only be called before init()"

    def g(self, *args, **kw):
        if self._initialised:
            raise UnavailableAfterInit()

        return f(self, *args, **kw)

    return g

class Robot(object):
    """Class for initialising and accessing robot hardware"""
    SYSLOCK_PATH = "/tmp/robot-object-lock"

    def __init__( self,
                  quiet = False,
                  init = True):

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
        #self._init_vision()
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


    '''def _init_vision(self):
        udev = pyudev.Context()
        cams = list(udev.list_devices( subsystem="video4linux",
                                       # For now, find devices that use this driver
                                       ID_USB_DRIVER="uvcvideo" ))

        if len(cams) == 0:
            "Camera isn't connected."
            return

        camdev = cams[0].device_node

        # Find libkoki.so:
        libpath = None
        if "LD_LIBRARY_PATH" in os.environ:
            for d in os.environ["LD_LIBRARY_PATH"].split(":"):
                l = glob.glob( "%s/libkoki.so*" % os.path.abspath( d ) )

                if len(l):
                    libpath = os.path.abspath(d)
                    break

        if libpath == None:
            v = vision.Vision(camdev, "/usr/lib")
        else:
            v = vision.Vision(camdev, libpath)

        self.vision = v

    def see(self, res = (800,600), stats = False):
        if not hasattr( self, "vision" ):
            raise NoCameraPresent()

        return self.vision.see( res = res,
                                mode = self.mode,
                                arena = self.arena,
                                stats = stats )'''
