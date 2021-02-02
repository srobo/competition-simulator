from math import tau, atan2

from controller import Robot, Compass as WebotsCompass
from sr.robot.utils import get_robot_device


class Compass:
    def __init__(self, webot: Robot):
        self._compass = get_robot_device(webot, "robot compass", WebotsCompass)
        self._compass.enable(int(webot.getBasicTimeStep()))

    def get_heading(self) -> float:
        """
        Return the heading from the compass in the range 0 - 2pi
        """
        x, _, z = self._compass.getValues()
        return atan2(x, z) % tau
