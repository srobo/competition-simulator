from sr.robot.utils import map_to_range
from sr.robot.settings import TIME_STEP
from sr.robot.randomizer import add_jitter


class SensorBase(object):

    def __init__(self, webot, sensor_name):
        self.webot = webot
        self.sensor_name = sensor_name


class DistanceSensor(SensorBase):

    LOWER_BOUND = 0
    UPPER_BOUND = 0.3

    def __init__(self, webot, sensor_name):
        super().__init__(webot, sensor_name)
        self.webot_sensor = self.webot.getDistanceSensor(self.sensor_name)
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


class Microswitch(SensorBase):

    def __init__(self, webot, sensor_name):
        super().__init__(webot, sensor_name)
        self.webot_sensor = self.webot.getTouchSensor(self.sensor_name)
        self.webot_sensor.enable(TIME_STEP)

    def read_value(self):
        return self.webot_sensor.getValue() > 0


class Led(object):

    def __init__(self, webot, device_name):
        self.webot = webot
        self.device_name = device_name
        self.webot_sensor = self.webot.getLED(self.device_name)

    def read_value(self):
        return self.webot_sensor.get() > 0

    def write_value(self, value):
        self.webot_sensor.set(value)
