from __future__ import annotations

from controller import Robot
from sr.robot3.utils import map_to_range
from sr.robot3.randomizer import add_jitter
from sr.robot3.motor_devices import Wheel, Gripper, LinearMotor

# The maximum value that the motor board will accept
SPEED_MAX = 1

COAST = 0
BRAKE = 0


def init_motor_boards(webot: Robot) -> dict[str, MotorBoard]:
    return {
        'srABC1': MotorBoard(
            Wheel(webot, 'left wheel'),
            Wheel(webot, 'right wheel'),
        ),
    }


def translate(sr_speed_val: float, sr_motor: Gripper | Wheel | LinearMotor) -> float:
    # Translate from -1 to 1 range to the actual motor control range

    if sr_speed_val != 0:
        sr_speed_val = add_jitter(sr_speed_val, -SPEED_MAX, SPEED_MAX)

    return map_to_range(
        (-SPEED_MAX, SPEED_MAX),
        (-sr_motor.max_speed, sr_motor.max_speed),
        sr_speed_val,
    )


class MotorBoard:
    """Represents a motor board."""

    def __init__(
        self,
        m0: Wheel | LinearMotor | Gripper | None,
        m1: Wheel | LinearMotor | Gripper | None,
    ) -> None:
        self.m0 = MotorChannel(0, m0)
        self.m1 = MotorChannel(1, m1)

        self.motors = [
            MotorChannel(0, m0),
            MotorChannel(1, m1),
        ]


class MotorChannel:
    """Represents a motor output channel."""

    def __init__(
        self,
        channel: int,
        sr_motor: Gripper | Wheel | LinearMotor | None,
    ) -> None:
        self.channel = channel

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

        if value > SPEED_MAX or value < -SPEED_MAX:
            raise ValueError(
                f"Motor power must be between {SPEED_MAX} and -{SPEED_MAX}.",
            )

        if self.sr_motor:
            self.sr_motor.set_speed(translate(value, self.sr_motor))
