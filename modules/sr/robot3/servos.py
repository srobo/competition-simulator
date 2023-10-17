from __future__ import annotations

import dataclasses
from collections.abc import Mapping

from controller import Motor, Robot
from sr.robot3.utils import map_to_range, get_robot_device

SERVO_LIMIT = 1


def init_servo_board(webot: Robot) -> dict[str, ServoBoard]:
    return {
        'srXYZ2': ServoBoard({
            0: Servo(webot, 'left gripper'),
            1: Servo(webot, 'right gripper'),
            2: Servo(webot, 'left finger'),
            3: Servo(webot, 'right finger'),
        }),
    }


class ServoBoard:
    _VALID_PINS = range(12)

    def __init__(self, servos: Mapping[int, Servo]) -> None:
        invalid_servos = [x for x in servos.keys() if x not in self._VALID_PINS]
        if invalid_servos:
            raise ValueError(f"Invalid servos: {invalid_servos}")

        self.servos: tuple[Servo | NullServo, ...] = tuple(
            servos.get(x) or NullServo() for x in self._VALID_PINS
        )


@dataclasses.dataclass
class NullServo:
    position: float | None = 0.0


class Servo:
    def __init__(self, webot: Robot, servo_name: str) -> None:
        self._servo = ServoDevice(webot, servo_name)
        self._position = 0.0

    @property
    def position(self) -> float:
        return self._position

    @position.setter
    def position(self, value: None | float) -> None:
        if value is not None:
            self._position = value
            self._servo.set_position(value)


class ServoDevice:
    def __init__(self, webot: Robot, servo_name: str) -> None:
        self.servo_name = servo_name
        self.webot_motor = get_robot_device(webot, servo_name, Motor)
        self.max_speed = self.webot_motor.getMaxVelocity()
        self.max_position = self.webot_motor.getMaxPosition()
        self.min_position = self.webot_motor.getMinPosition()

    def set_position(self, position: float) -> None:
        if position > SERVO_LIMIT or position < -SERVO_LIMIT:
            raise ValueError(
                f"Servo position must be between {SERVO_LIMIT} and -{SERVO_LIMIT}.",
            )

        self.webot_motor.setPosition(map_to_range(
            (-1, 1),
            (self.min_position + 0.001, self.max_position - 0.001),
            position,
        ))
