from __future__ import annotations

from typing import Dict, List, Union

from controller import Motor, Robot
from sr.robot3.utils import map_to_range, get_robot_device


def init_servo_board(webot: Robot) -> 'Dict[str, ServoBoard]':
    return {
        'srXYZ2': ServoBoard([
            Servo(webot, 'left gripper'),
            Servo(webot, 'right gripper'),
        ]),
    }


class ServoBoard:
    def __init__(self, servos: 'List[Servo]') -> None:
        self.servos = servos


class Servo:
    def __init__(self, webot: Robot, servo_name: str) -> None:
        self._servo = ServoDevice(webot, servo_name)
        self._position = 0.0

    @property
    def position(self) -> float:
        return self._position

    @position.setter
    def position(self, value: Union[None, float]) -> None:
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
        self.webot_motor.setPosition(map_to_range(
            -1,
            1,
            self.min_position + 0.001,
            self.max_position - 0.001,
            position,
        ))
