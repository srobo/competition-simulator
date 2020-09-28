from typing import List, Union

from controller import Robot
from sr.robot.utils import map_to_range
from sr.robot.randomizer import add_jitter
from sr.robot.motor_devices import Wheel, Gripper, LinearMotor

# The maximum value that the motor board will accept
SPEED_MAX = 100


def init_motor_array(webot: Robot) -> 'List[Motor]':
    return [
        Motor(
            Wheel(webot, 'left wheel'),
            Wheel(webot, 'right wheel'),
        ),
        Motor(
            LinearMotor(webot, 'lift motor'),
            Gripper(webot, 'left finger motor|right finger motor'),
        ),
    ]


def translate(sr_speed_val, sr_motor):
    # Translate from -100 to 100 range to the actual motor control range

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

    def __init__(self, m0: Union[Wheel, LinearMotor], m1: Union[Wheel, Gripper]) -> None:
        self.m0 = MotorChannel(0, m0)
        self.m1 = MotorChannel(1, m1)


class MotorChannel:
    """Represents a motor output channel."""

    def __init__(self, channel: int, sr_motor: Union[Gripper, Wheel, LinearMotor]) -> None:
        self.channel = channel
        # Private shadow of use_brake
        # self._use_brake = True # TODO create new thread for non-braking slowdown

        # There is currently no method for reading the power from a motor board
        self._power = 0
        self.sr_motor = sr_motor

    @property
    def power(self):
        """Get or set the level of power for this motor channel."""
        return self._power

    @power.setter
    def power(self, value):
        "target setter function"
        value = int(value)
        self._power = value

        # Limit the value to within the valid range
        if value > SPEED_MAX:
            value = SPEED_MAX
        elif value < -SPEED_MAX:
            value = -SPEED_MAX

        self.sr_motor.set_speed(translate(value, self.sr_motor))

