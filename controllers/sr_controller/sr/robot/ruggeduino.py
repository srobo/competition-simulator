from sr.robot.sensor_devices import Microswitch, DistanceSensor


def init_ruggeduino_array(webot):
    dist_sensor_names = [
        "Front Left DS",
        "Front Right DS",
        "Left DS",
        "Right DS",
        "Back Left DS",
        "Back Right DS",
    ]
    switch_names = [
        "front bump sensor",
        "back bump sensor",
        "token bump sensor",
        "left finger sensor",
        "right finger sensor",
    ]

    analogue_array = [DistanceSensor(webot, name) for name in dist_sensor_names]

    digital_array = [Microswitch(webot, name) for name in switch_names]

    return [Ruggeduino(analogue_array, digital_array)]


class Ruggeduino(object):

    DIGITAL_PIN_OFFSET = 2  # Exclude pins 0 and 1 as they are used for USB serial comms

    def __init__(self, analogue_array, digital_array):
        self._analogue_array = analogue_array
        self._digital_array = digital_array

    def digital_read(self, pin):
        "Read an digital input"
        if pin < 2 or pin > 13:
            raise ValueError("Only pins 2 - 13 are available on the Ruggeduino")
        return self._digital_array[pin - Ruggeduino.DIGITAL_PIN_OFFSET].read_value()

    def digital_write(self, pin, level):
        "Write to an output"
        raise NotImplementedError("This robot does not support digital_write")

    def analogue_read(self, pin):
        "Read an analogue input"
        return self._analogue_array[pin].read_value()

    def pin_mode(self, pin_no, mode):
        raise NotImplementedError(
            "The sensors are pre-set on this robot so you don't need to set the pin mode",
        )
