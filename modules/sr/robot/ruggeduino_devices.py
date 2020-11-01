import logging

from controller import Robot
from sr.robot.utils import map_to_range
from sr.robot.randomizer import add_jitter

LOGGER = logging.getLogger(__name__)


class DistanceSensor:

    LOWER_BOUND = 0
    UPPER_BOUND = 0.3

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = webot.getDistanceSensor(sensor_name)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def __get_scaled_distance(self):
        return map_to_range(
            self.webot_sensor.getMinValue(),
            self.webot_sensor.getMaxValue(),
            DistanceSensor.LOWER_BOUND,
            DistanceSensor.UPPER_BOUND,
            self.webot_sensor.getValue(),
        )

    def read_value(self):
        return add_jitter(
            self.__get_scaled_distance(),
            DistanceSensor.LOWER_BOUND,
            DistanceSensor.UPPER_BOUND,
        )


class Microswitch:

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = webot.getTouchSensor(sensor_name)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def read_value(self):
        return self.webot_sensor.getValue() > 0


class Led:

    def __init__(self, webot, device_name, limiter) -> None:
        self._name = device_name
        self.webot_sensor = webot.getLED(device_name)
        self._limiter = limiter

    def write_value(self, value):
        if not self._limiter.can_change():
            LOGGER.warning(
                "Rate limited change to LED output (requested setting %s to %r)",
                self._name,
                value,
            )
            return

        self.webot_sensor.set(value)
