from sr.robot.ruggeduino_devices import Led, Microswitch, DistanceSensor


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
    led_names = [
        "led 1",
        "led 2",
        "led 3",
        "led 4",
        "led 5",
        "led 6",
    ]

    analogue_input_array = [DistanceSensor(webot, name) for name in dist_sensor_names]

    digital_input_array = [Microswitch(webot, name) for name in switch_names]

    digital_output_array = [Led(webot, name) for name in led_names]

    return [Ruggeduino(webot, analogue_input_array, digital_input_array, digital_output_array)]


class Ruggeduino(object):

    DIGITAL_READ_PIN_START = 2

    def __init__(self, webot, analogue_input_array, digital_input_array, digital_output_array):
        self.webot = webot
        self.analogue_input_array = analogue_input_array
        self.digital_input_array = digital_input_array
        self.digital_output_array = digital_output_array

    def digital_read(self, pin):
        "Read an digital input"
        return self.digital_input_array[pin - Ruggeduino.DIGITAL_READ_PIN_START].read_value()

    def digital_write(self, pin, level):
        "Write a digital output"
        array_index = pin - Ruggeduino.DIGITAL_READ_PIN_START - len(self.digital_input_array)
        print(array_index)
        return self.digital_output_array[array_index].write_value(level)

    def analogue_read(self, pin):
        "Read an analogue input"
        return self.analogue_input_array[pin].read_value()

    def pin_mode(self, pin_no, mode):
        raise NotImplementedError(
            "The sensors are pre-set on this robot so you don't need to set the pin mode",
        )
