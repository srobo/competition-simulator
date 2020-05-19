from sr.robot.randomizer import add_jitter
from sr.robot.sensor_devices import DistanceSensor, Microswitch

MIN_VOLTS = 0
MAX_VOLTS = 5

def init_ruggeduino_array(webot):
    analogue_array = []
    analogue_array.append(DistanceSensor(webot, "Front Left DS"))
    analogue_array.append(DistanceSensor(webot, "Front Right DS"))
    analogue_array.append(DistanceSensor(webot, "Left DS"))
    analogue_array.append(DistanceSensor(webot, "Right DS"))
    analogue_array.append(DistanceSensor(webot, "Back Left DS"))
    analogue_array.append(DistanceSensor(webot, "Back Right DS"))

    digital_array = []
    digital_array.append(Microswitch(webot, "front bump sensor"))
    digital_array.append(Microswitch(webot, "back bump sensor"))
    digital_array.append(Microswitch(webot, "token bump sensor"))
    digital_array.append(Microswitch(webot, "left finger sensor"))
    digital_array.append(Microswitch(webot, "right finger sensor"))

    return [Ruggeduino(webot, analogue_array, digital_array)]

class Ruggeduino(object):
    def __init__(self, webot, analogue_array, digital_array):
        self.webot = webot
        self.analogue_array = analogue_array
        self.digital_array = digital_array
        self.DIGITAL_PIN_OFFSET = 2 # not to use pins 0 or 1 because they're tx and rx

    def digital_read(self, pin):
        "Read an digital input"
        return self.digital_array[pin - self.DIGITAL_PIN_OFFSET].read_value()

    def digital_write(self, pin, level):
        "Write to an output"
        raise NotImplementedError("This robot does not support digital_write")

    def analogue_read(self, pin):
        "Read an analogue input"
        return add_jitter(self.analogue_array[pin].read_value(), MIN_VOLTS, MAX_VOLTS)
