from typing import Dict, Union

from controller import Robot
from sr.robot.utils import map_to_range
from sr.robot.randomizer import add_jitter
from sr.robot.motor_devices import Wheel, Gripper, LinearMotor

# The maximum value that the motor board will accept
SPEED_MAX = 1.0

COAST = 0
BRAKE = 0


def init_motor_array(webot: Robot) -> 'Dict[str, Motor]':
    return {
        'srABC1': Motor(
            Wheel(webot, 'left wheel'),
            Wheel(webot, 'right wheel'),
        ),
    }


def translate(sr_speed_val: float, sr_motor: Union[Gripper, Wheel, LinearMotor]) -> float:
    # Translate from -1 to 1 range to the actual motor control range

    if sr_speed_val != 0:
        sr_speed_val = add_jitter(sr_speed_val, -SPEED_MAX, SPEED_MAX)

    return map_to_range(
        -SPEED_MAX,
        SPEED_MAX,
        -sr_motor.max_speed,
        sr_motor.max_speed,
        sr_speed_val,
    )


class Motor:
    """Represents a motor board."""

    def __init__(
        self,
        m0: Union[Wheel, LinearMotor, Gripper, None],
        m1: Union[Wheel, LinearMotor, Gripper, None],
    ) -> None:
        self.m0 = MotorChannel(0, m0)
        self.m1 = MotorChannel(1, m1)

        self.motors = [
            MotorChannel(0, m0),
            MotorChannel(1, m1),
        ]


class MotorChannel:
    """Represents a motor output channel."""

    def __init__(self, channel: int, sr_motor: Union[Gripper, Wheel, LinearMotor, None]) -> None:
        self.channel = channel
        # Private shadow of use_brake
        # self._use_brake = True # TODO create new thread for non-braking slowdown

        # There is currently no method for reading the power from a motor board
        self._power = 0.0
        self.sr_motor = sr_motor

    @property
    def power(self) -> float:
        """Get or set the level of power for this motor channel."""
        return self._power

    @power.setter
    def power(self, value: float) -> None:
        "target setter function"
        self._power = value

        # Limit the value to within the valid range
        if value > SPEED_MAX:
            value = SPEED_MAX
        elif value < -SPEED_MAX:
            value = -SPEED_MAX

        if self.sr_motor:
            self.sr_motor.set_speed(translate(value, self.sr_motor))

    ''''@property
    def use_brake(self) -> bool:
        "Whether to use the brake when at 0 speed"
        return self._use_brake

    @use_brake.setter
    def use_brake(self, value: bool) -> None:
        self._use_brake = value

        if self.power == 0:
            "Implement the new braking setting"
            self.power = 0'''
