from sr.robot.settings import TIME_STEP

class SensorBase(object):

    MIN_VOLTS = 0
    MAX_VOLTS = 5

    def __init__(self, webot, sensor_name):
        self.webot = webot
        self.sensor_name = sensor_name

class DistanceSensor(SensorBase):

    def __init__(self, webot, sensor_name):
        super().__init__(webot, sensor_name)
        self.webot_sensor = self.webot.getDistanceSensor(self.sensor_name)
        self.webot_sensor.enable(TIME_STEP)

    def __scale_to_voltage(self, val):
        old_max = self.webot_sensor.getMaxValue()
        old_min = self.webot_sensor.getMinValue()
        new_max = SensorBase.MAX_VOLTS
        new_min = SensorBase.MIN_VOLTS
        return ( (val - old_min) / (old_max - old_min) ) * (new_max - new_min) + new_min
         

    def read_value(self):
        return self.__scale_to_voltage(self.webot_sensor.getValue())

class Microswitch(SensorBase):

    def __init__(self, webot, sensor_name):
        super().__init__(webot, sensor_name)
        self.webot_sensor = self.webot.getTouchSensor(self.sensor_name)
        self.webot_sensor.enable(TIME_STEP)

    def read_value(self):
        return self.webot_sensor.getValue() > 0

