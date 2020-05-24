from sr.robot.sensor_devices import DistanceSensor, Microswitch

def init_ruggeduino_array(webot):
    distSensorNames = ["Front Left DS", "Front Right DS", "Left DS", "Right DS", "Back Left DS", "Back Right DS"]
    switchNames = ["front bump sensor", "back bump sensor", "token bump sensor", "left finger sensor", "right finger sensor"]

    analogue_array = [DistanceSensor(webot, name) for name in distSensorNames]

    digital_array = [Microswitch(webot, name) for name in switchNames]

    return [Ruggeduino(webot, analogue_array, digital_array)]

class Ruggeduino(object):
    
    DIGITAL_PIN_OFFSET = 2 # Exclude pins 0 and 1 as they are used for USB serial comms

    def __init__(self, webot, analogue_array, digital_array):
        self.webot = webot
        self.analogue_array = analogue_array
        self.digital_array = digital_array

    def digital_read(self, pin):
        "Read an digital input"
        if pin < 2 or pin > 13:
            raise ValueError("Only pins 2 - 13 are available on the Ruggeduino")
        return self.digital_array[pin - Ruggeduino.DIGITAL_PIN_OFFSET].read_value()

    def digital_write(self, pin, level):
        "Write to an output"
        raise NotImplementedError("This robot does not support digital_write")

    def analogue_read(self, pin):
        "Read an analogue input"
        return self.analogue_array[pin].read_value()
