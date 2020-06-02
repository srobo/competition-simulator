from abc import ABC, abstractmethod

from sr.robot.utils import map_to_range
from sr.robot.settings import TIME_STEP
from sr.robot.randomizer import add_jitter


class SensorBase(ABC):
    @abstractmethod
    def read_value(self):
        pass


class DistanceSensor(SensorBase):

    LOWER_BOUND = 0
    UPPER_BOUND = 0.3

    def __init__(self, webot, sensor_name):
        self.__webot_sensor = webot.getDistanceSensor(sensor_name)
        self.__webot_sensor.enable(TIME_STEP)

    def __get_scaled_distance(self):
        return map_to_range(
            self.__webot_sensor.getMinValue(),
            self.__webot_sensor.getMaxValue(),
            DistanceSensor.LOWER_BOUND,
            DistanceSensor.UPPER_BOUND,
            self.__webot_sensor.getValue(),
        )

    def read_value(self):
        return add_jitter(
            self.__get_scaled_distance(),
            DistanceSensor.LOWER_BOUND,
            DistanceSensor.UPPER_BOUND,
        )


class Microswitch(SensorBase):

    def __init__(self, webot, sensor_name):
        self.__webot_sensor = webot.getTouchSensor(sensor_name)
        self.__webot_sensor.enable(TIME_STEP)

    def read_value(self):
        return self.__webot_sensor.getValue() > 0
