from __future__ import annotations

import math
import random
from typing import TypeVar, Collection
from pathlib import Path
from threading import Lock

from sr.robot3 import motor, power, april_camera, servos, metadata, ruggeduino
# Webots specific library
from controller import Robot as WebotsRobot

T = TypeVar('T')


class Robot:
    """
    Primary API for access to robot parts.

    This robot requires that the consumer manage the progression of time
    manually by calling the `sleep` method.
    """

    def __init__(
        self,
        *,
        auto_start: bool = False,
        verbose: bool = False,
        env: object = None,
        ignored_ruggeduinos: list[str] | None = None,
    ) -> None:
        """
        Initialise robot.

        Note: `env` and `ignored_ruggeduinos` are ignored in the simulator.
        """

        self._quiet = not verbose

        self._webot = WebotsRobot()
        # returns a float, but should always actually be an integer value
        self._timestep = int(self._webot.getBasicTimeStep())

        self._metadata, self._code_path = metadata.init_metadata()

        # Lock used to guard access to Webot's time stepping machinery, allowing
        # us to safely advance simulation time from *either* the competitor's
        # code (in the form of our `sleep` method) or from our background
        # thread, but not both.
        self._step_lock = Lock()

        self._init_devs()
        self.display_info()

        if not auto_start:
            self.wait_start()

    def _get_user_code_info(self) -> str | None:
        user_version_path = self._code_path / '.user-rev'
        try:
            return user_version_path.read_text().strip()
        except IOError:
            return None

    def display_info(self) -> None:
        user_code_version = self._get_user_code_info()

        parts = [
            f"Zone: {self.zone}",
            f"Mode: {self.mode}",
        ]

        if user_code_version:
            parts.append(f"User code: {user_code_version}")

        print("Robot Initialized. {}.".format(", ".join(parts)))  # noqa: T201

    def webots_step_and_should_continue(self, duration_ms: int) -> bool:
        """
        Run a webots step of the given duration in milliseconds.

        Returns whether or not the simulation should continue (based on
        Webots telling us whether or not the simulation is about to end).
        """

        if duration_ms <= 0:
            raise ValueError(
                f"Duration must be greater than zero, not {duration_ms!r}",
            )

        with self._step_lock:
            # We use Webots in synchronous mode (specifically
            # `synchronization` is left at its default value of `TRUE`). In
            # that mode, Webots returns -1 from step to indicate that the
            # simulation is terminating, or 0 otherwise.
            result = self._webot.step(duration_ms)
            return result != -1

    def print_wifi_details(self) -> None:
        print("The simulated robot does not have WiFi.")  # noqa: T201

    def wait_start(self) -> None:
        "Wait for the start signal to happen"

        print("Waiting for start signal.")  # noqa: T201

        # Always advance time by a little bit. This simulates the real-world
        # condition that the wait-start mechanism would always wait for the
        # start button.
        self.webots_step_and_should_continue(
            self._timestep * random.randint(8, 20),
        )

        if self.mode == metadata.RobotMode.COMP:
            # Interact with the supervisor "robot" to wait for the start of the match.
            self._webot.setCustomData('ready')
            while (
                self._webot.getCustomData() != 'start' and
                self.webots_step_and_should_continue(self._timestep)
            ):
                pass

        print("Starting")  # noqa: T201

    def _init_devs(self) -> None:
        "Initialise the attributes for accessing devices"

        # Power boards
        self._init_power_board()

        # Motor boards
        self._init_motors()

        # Servo boards
        self._init_servos()

        # Ruggeduinos
        self._init_ruggeduinos()

        # Camera
        self._init_cameras()

    def _init_power_board(self) -> None:
        self.power_board = power.init_power_board(self)

    def _init_motors(self) -> None:
        self.motor_boards = motor.init_motor_array(self._webot)

    def _init_servos(self) -> None:
        self.servo_boards = servos.init_servo_board(self._webot)

    def _init_ruggeduinos(self) -> None:
        self.ruggeduinos = ruggeduino.init_ruggeduino_array(self._webot)

    def _init_cameras(self) -> None:
        # See comment in WebotsCameraSource.read for why we need to pass the step lock here.
        self._cameras = april_camera.init_cameras(self._webot, self._step_lock)

    def _singular(self, elements: Collection[T], name: str) -> T:
        num = len(elements)
        if num != 1:
            raise ValueError(f"Expected exactly one {name} to be connected, but found {num}")
        x, = elements
        return x

    @property
    def camera(self) -> april_camera.AprilCameraBoard:
        return self._singular(self._cameras, 'camera')

    @property
    def motor_board(self) -> motor.MotorBoard:
        return self._singular(self.motor_boards.values(), 'motor board')

    @property
    def ruggeduino(self) -> ruggeduino.Ruggeduino:
        return self._singular(self.ruggeduinos.values(), 'ruggeduino')

    @property
    def servo_board(self) -> servos.ServoBoard:
        return self._singular(self.servo_boards.values(), 'servo board')

    @property
    def arena(self) -> str:
        return self.metadata.arena

    @property
    def mode(self) -> metadata.RobotMode:
        return self.metadata.mode

    @property
    def usbkey(self) -> Path | None:
        return self._code_path

    @property
    def zone(self) -> int:
        return self.metadata.zone

    @property
    def is_simulated(self) -> bool:
        """
        Determine whether the robot is simulated.

        :returns: True if the robot is simulated. False otherwise.
        """
        return True

    @property
    def metadata(self) -> metadata.Metadata:
        return self._metadata

    def time(self) -> float:
        """
        Roughly equivalent to `time.time` but for simulation time.
        """
        return self._webot.getTime()

    def sleep(self, secs: float) -> None:
        """
        Roughly equivalent to `time.sleep` but accounting for simulation time.
        """
        # Checks that secs is positive or zero
        if secs < 0:
            raise ValueError('sleep length must be non-negative')

        # Ensure the time delay is a valid step increment, while also ensuring
        # that small values remain non-zero.
        n_steps = math.ceil((secs * 1000) / self._timestep)
        duration_ms = n_steps * self._timestep

        # Assume that we're in the main thread here, so we don't really need to
        # do any cleanup if Webots tells us the simulation is terminating. When
        # webots kills the process all the proper tidyup will happen anyway.
        self.webots_step_and_should_continue(duration_ms)
