from sr.robot.settings import TIME_STEP
from sr.robot.utils import map_to_range
from sr.robot.randomizer import add_jitter


class SensorBase(object):

    def __init__(self, webot, sensor_name):
        self.webot = webot
        self.sensor_name = sensor_name


class DistanceSensor(SensorBase):

    LOWER_BOUNDS = 0
    UPPER_BOUNDS = 0.3

    def __init__(self, webot, sensor_name):
        super().__init__(webot, sensor_name)
        self.webot_sensor = self.webot.getDistanceSensor(self.sensor_name)
        self.webot_sensor.enable(TIME_STEP)

    def __get_scaled_distance(self):
        val = self.webot_sensor.getValue()
        return map_to_range(self.webot_sensor.getMinValue(), self.webot_sensor.getMaxValue(), DistanceSensor.LOWER_BOUNDS, DistanceSensor.UPPER_BOUNDS, val)

    def read_value(self):
        return add_jitter(
            self.__get_scaled_distance(),
            DistanceSensor.LOWER_BOUNDS,
            DistanceSensor.UPPER_BOUNDS,
        )


class Microswitch(SensorBase):

    def __init__(self, webot, sensor_name):
        super().__init__(webot, sensor_name)
        self.webot_sensor = self.webot.getTouchSensor(self.sensor_name)
        self.webot_sensor.enable(TIME_STEP)

    def read_value(self):
        return self.webot_sensor.getValue() > 0
