from sr.robot.settings import TIME_STEP

class SensorBase(object):

    def __init__(self, webot, sensor_name):
        self.webot = webot
        self.sensor_name = sensor_name

class DistanceSensor(SensorBase):

    def __init__(self, webot, sensor_name):
        super().__init__(webot, sensor_name)
        self.webot_sensor = self.webot.getDistanceSensor(self.sensor_name)
        self.webot_sensor.enable(TIME_STEP)

    def __scale_to_voltage(self, val):
        return val * 0.5 / 100

    def read_value(self):
        return self.__scale_to_voltage(self.webot_sensor.getValue())

class Microswitch(SensorBase):

    def __init__(self, webot, sensor_name):
        super().__init__(webot, sensor_name)
        self.webot_sensor = self.webot.getTouchSensor(self.sensor_name)
        self.webot_sensor.enable(TIME_STEP)

    def read_value(self):
        return self.webot_sensor.getValue() > 0

