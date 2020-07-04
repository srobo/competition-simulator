import time
from os import path, environ
from typing import Optional
from threading import Lock, Thread

from sr.robot import motor, camera, ruggeduino

# Webots specific library
from controller import Robot as WebotsRobot  # isort:skip


class ManualTimestepRobot:
    """
    Class for initialising and accessing robot hardware.

    This robot requires that the consumer manage the progession of time manually
    by calling the `sleep` method.
    """

    def __init__(self, quiet: bool = False, init: bool = True) -> None:
        self._initialised = False
        self._quiet = quiet

        self.webot = WebotsRobot()
        # returns a float, but should always actually be an integer value
        self._timestep = int(self.webot.getBasicTimeStep())

        self.mode = environ.get("SR_ROBOT_MODE", "dev")
        self.zone = int(environ.get("SR_ROBOT_ZONE", 0))
        self.arena = "A"
        self.usbkey = path.normpath(path.join(environ["SR_ROBOT_FILE"], "../"))

        # Lock used to guard access to Webot's time stepping machinery, allowing
        # us to safely advance simulation time from *either* the competitor's
        # code (in the form of our `sleep` method) or from our background
        # thread, but not both.
        self._step_lock = Lock()

        if init:
            self.init()
            self.wait_start()

    @classmethod
    def setup(cls):
        return cls(init=False)

    def init(self) -> None:
        self._init_devs()
        self._initialised = True
        self.display_info()

    def _get_user_code_info(self) -> Optional[str]:
        user_version_path = path.join(self.usbkey, '.user-rev')
        if path.exists(user_version_path):
            with open(user_version_path) as f:
                return f.read().strip()

        return None

    def display_info(self) -> None:
        user_code_version = self._get_user_code_info()

        parts = [
            "Zone: {}".format(self.zone),
            "Mode: {}".format(self.mode),
        ]

        if user_code_version:
            parts.append("User code: {}".format(user_code_version))

        print("Robot Initialized. {}.".format(", ".join(parts)))  # noqa:T001

    def webots_step_and_should_continue(self, duration_ms: int) -> bool:
        """
        Run a webots step of the given duration in milliseconds.

        Returns whether or not the simulation should continue (based on
        Webots telling us whether or not the simulation is about to end).
        """

        with self._step_lock:
            # We use Webots in synchronous mode (specifically
            # `synchronization` is left at its default value of `TRUE`). In
            # that mode, Webots returns -1 from step to indicate that the
            # simulation is terminating, or 0 otherwise.
            result = self.webot.step(duration_ms)
            return result != -1

    def wait_start(self) -> None:
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

    def _init_devs(self) -> None:
        "Initialise the attributes for accessing devices"

        # Motor boards
        self._init_motors()

        # Ruggeduinos
        self._init_ruggeduinos()

        # Camera
        self._init_camera()

    def _init_motors(self) -> None:
        self.motors = motor.init_motor_array(self.webot)

    def _init_ruggeduinos(self) -> None:
        self.ruggeduinos = ruggeduino.init_ruggeduino_array(self.webot)

    def _init_camera(self) -> None:
        # See comment in Camera.see for why we need to pass the step lock here.
        self.camera = camera.Camera(self.webot, self._step_lock)
        self.see = self.camera.see

    def time(self) -> float:
        """
        Roughly equivalent to `time.time` but for simulation time.
        """
        return self.webot.getTime()

    def sleep(self, secs: float) -> None:
        """
        Roughly equivalent to `time.sleep` but accounting for simulation time.
        """
        # Checks that secs is positive or zero
        if secs < 0:
            raise ValueError('sleep length must be non-negative')

        # Ensure the time delay is a valid step increment
        n_steps = int((secs * 1000) // self._timestep)
        duration_ms = n_steps * self._timestep

        # We're in the main thread here, so we don't really need to do any
        # cleanup if Webots tells us the simulation is terminating. When webots
        # kills the process all the proper tidyup will happen anyway.
        self.webots_step_and_should_continue(duration_ms)


class AutomaticTimestepRobot(ManualTimestepRobot):
    """
    Robot class which preserves the original automatic time-advancing behaviour.

    This class launches a background thread which advances the timestep in a
    tight loop. This is somewhat more convenient to program against because it
    does not rely on the `sleep` method being called in order for time to
    advance. However as a result the timestep is considerably less predictable
    which can result in unexpected robot behaviours.

    The `sleep` method of this class is still available and is thread-safe.
    """

    def init(self) -> None:
        self.webots_init()
        super().init()

    def webots_init(self) -> None:
        # Create a thread which will advance time in the background, so that the
        # competitors' code can ignore the fact that it is actually running in a
        # simulation.
        t = Thread(
            target=self.webot_run_robot,
            # Ensure our background thread alone won't keep the controller
            # process runnnig.
            daemon=True,
        )
        t.start()
        time.sleep(self._timestep / 1000)

    def webot_run_robot(self):
        while self.webots_step_and_should_continue(self._timestep):
            pass
