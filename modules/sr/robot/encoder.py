from __future__ import annotations

from typing import List

from controller import Robot, PositionSensor
from shared_utils import RobotType
from sr.robot.utils import get_robot_device


def init_encoder_array(webot: Robot, robot_type: RobotType) -> List[Encoder]:
    if robot_type == RobotType.FORKLIFT:
        return [
            RotaryEncoder(webot, 'left wheel sensor'),
            RotaryEncoder(webot, 'right wheel sensor'),

            LinearEncoder(webot, 'left gripper sensor'),
            LinearEncoder(webot, 'right gripper sensor'),
        ]
    else:
        return [
            LinearEncoder(webot, 'bridge position sensor'),
            LinearEncoder(webot, 'trolley position sensor'),
            LinearEncoder(webot, 'hoist position sensor'),
        ]


class Encoder:
    def __init__(self, webot: Robot, sensor_name: str):
        self._encoder = get_robot_device(webot, sensor_name, PositionSensor)
        self._encoder.enable(int(webot.getBasicTimeStep()))


class RotaryEncoder(Encoder):
    @property
    def rotation(self) -> float:
        """
        Get the accumulated rotational movement in radians of the associated joint
        """
        return self._encoder.getValue()


class LinearEncoder(Encoder):
    @property
    def displacement(self) -> float:
        """
        Get the linear movement in meters from the joint's default position
        """
        return self._encoder.getValue()
