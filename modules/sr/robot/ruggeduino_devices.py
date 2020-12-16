import logging

from controller import (
    LED,
    Robot,
    TouchSensor,
    DistanceSensor as TDistanceSensor,
)
from sr.robot.utils import map_to_range, get_robot_device
from sr.robot.randomizer import add_jitter
from sr.robot.output_frequency_limiter import OutputFrequencyLimiter

LOGGER = logging.getLogger(__name__)


class DistanceSensor:
    """
    A standard Webots distance sensor,  we convert the distance to metres.
    """

    LOWER_BOUND = 0
    UPPER_BOUND = 2

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = get_robot_device(webot, sensor_name, TDistanceSensor)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def __get_scaled_distance(self) -> float:
        return map_to_range(
            self.webot_sensor.getMinValue(),
            self.webot_sensor.getMaxValue(),
            DistanceSensor.LOWER_BOUND,
            DistanceSensor.UPPER_BOUND,
            self.webot_sensor.getValue(),
        )

    def read_value(self) -> float:
        """
        Returns the distance measured by the sensor, in metres.
        """
        return add_jitter(
            self.__get_scaled_distance(),
            DistanceSensor.LOWER_BOUND,
            DistanceSensor.UPPER_BOUND,
        )


class Microswitch:
    """
    A standard Webots touch sensor.
    """

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = get_robot_device(webot, sensor_name, TouchSensor)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def read_value(self) -> bool:
        """
        Returns whether or not the touch sensor is in contact with something.
        """
        return self.webot_sensor.getValue() > 0


class Led:
    """
    A standard Webots LED.
    The value is a boolean to switch the LED on (True) or off (False).
    """

    def __init__(
        self,
        webot: Robot,
        device_name: str,
        limiter: OutputFrequencyLimiter,
    ) -> None:
        self._name = device_name
        self.webot_sensor = get_robot_device(webot, device_name, LED)
        self._limiter = limiter

    def write_value(self, value: bool) -> None:
        if not self._limiter.can_change():
            LOGGER.warning(
                "Rate limited change to LED output (requested setting %s to %r)",
                self._name,
                value,
            )
            return

        self.webot_sensor.set(value)
