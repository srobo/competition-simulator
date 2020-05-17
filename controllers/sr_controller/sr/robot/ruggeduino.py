from sr.robot.randomizer import add_jitter

DIST_SENSOR_NAMES = ["Front Left DS", "Front Right DS", "Left DS","Right DS", "Back Left DS", "Back Right DS"]
DS_TIME_STEP = 64
MIN_VOLTS = 0
MAX_VOLTS = 5

def init_ruggeduino_array(webot):
    init_dist_sensors(webot)
    return [Ruggeduino(webot)]

def init_dist_sensors(webot):
    for i in DIST_SENSOR_NAMES:
        sensor = webot.getDistanceSensor(i)
        if sensor != None:
            sensor.enable(DS_TIME_STEP)
        else:
            print("Not a valid sensor to init")

def dsScaleReadingToVoltage(val):
    return val * (0.5/100)

class Ruggeduino(object):
    """Class for talking to a Ruggeduino flashed with the SR firmware"""
    def __init__(self, webot):
        self.webot = webot

    def digital_read(self, pin):
        "Read a digital input"
        raise NotImplementedError("This robot does not support digital_read")

    def digital_write(self, pin, level):
        "Write to an output"
        raise NotImplementedError("This robot does not support digital_write")

    def analogue_read(self, pin):
        "Read an analogue input"
        sensor = self.webot.getDistanceSensor(DIST_SENSOR_NAMES[pin])
        if sensor != None:
            return add_jitter(float(dsScaleReadingToVoltage(sensor.getValue())), MIN_VOLTS, MAX_VOLTS)
        #else:
            #return "Not a valid sensor"
