from controller import Robot
from sr.robot.utils import map_to_range
from sr.robot.settings import TIME_STEP
from sr.robot.randomizer import add_jitter


class DistanceSensor:

    LOWER_BOUND = 0
    UPPER_BOUND = 0.3

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = webot.getDistanceSensor(sensor_name)
        self.webot_sensor.enable(TIME_STEP)

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
        self.webot_sensor.enable(TIME_STEP)

    def read_value(self):
        return self.webot_sensor.getValue() > 0
