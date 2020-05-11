DIST_SENSOR_NAMES = ["ds_left","ds_right"]
DS_TIME_STEP = 64

def init_ruggeduino_array(webot):
    init_dist_sensors(webot)
    return [Ruggeduino(webot)]

def init_dist_sensors(webot):
    for i in DIST_SENSOR_NAMES:
        sensor = webot.getDistanceSensor(i)
        if sensor != None:
            sensor.enable(DS_TIME_STEP)
        else:
            print "Not a valid sensor to init"

def dsScaleReadingtoMm(val):
    return val * (0.5/10)

class Ruggeduino(object):
    """Class for talking to a Ruggeduino flashed with the SR firmware"""
    def __init__(self, webot):
        self.webot = webot

    def digital_read(self, pin):
        "Read a digital input"

    def digital_write(self, pin, level):
        "Write to an output"

    def analogue_read(self, pin):
        "Read an analogue input"
        sensor = self.webot.getDistanceSensor(DIST_SENSOR_NAMES[pin])
        if sensor != None:
            return dsScaleReadingtoMm(sensor.getValue())
        #else:
            #return "Not a valid sensor"