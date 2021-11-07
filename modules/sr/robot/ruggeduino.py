from enum import Enum
from typing import Dict, Union

from controller import Robot
from sr.robot.ruggeduino_devices import Led, Microswitch, DistanceSensor
from sr.robot.output_frequency_limiter import OutputFrequencyLimiter

OUTPUT = 0
INPUT = 1
INPUT_PULLUP = 2


class AnaloguePin(Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"


ARDUINO_DEVICES_TYPE = Dict[Union[AnaloguePin, int], Union[DistanceSensor, Microswitch, Led]]


def init_ruggeduino_array(webot: Robot) -> 'Dict[str, Ruggeduino]':
    # The names in these arrays correspond to the names given to devices in Webots

    dist_sensor_names = [
        # Updating these? Also update controllers/example_controller/keyboard_controller.py
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
    ]
    led_names = [
        "led 1",
        "led 2",
        "led 3",
        "led 4",
        "led 5",
        "led 6",
    ]

    analogue_sensors = [
        DistanceSensor(webot, name)
        for name in dist_sensor_names
    ]
    analogue_input_dict: ARDUINO_DEVICES_TYPE = {
        key: sensor
        for key, sensor in zip(AnaloguePin, analogue_sensors)
    }

    digital_sensors = [
        Microswitch(webot, name)
        for name in switch_names
    ]
    digital_input_dict: ARDUINO_DEVICES_TYPE = {
        index: sensor
        for index, sensor in
        enumerate(digital_sensors, start=Ruggeduino.DIGITAL_PIN_START)
    }

    limiter = OutputFrequencyLimiter(webot)
    digital_outputs = [
        Led(webot, name, limiter, pin)
        for pin, name in enumerate(
            led_names,
            start=Ruggeduino.DIGITAL_PIN_START + len(digital_input_dict),
        )
    ]

    digital_output_dict: ARDUINO_DEVICES_TYPE = {
        index: output
        for index, output in enumerate(
            digital_outputs,
            start=Ruggeduino.DIGITAL_PIN_START + len(digital_input_dict),
        )
    }

    return {
        '0123456789': Ruggeduino({
            **analogue_input_dict,
            **digital_input_dict,
            **digital_output_dict,
        })
    }


class Ruggeduino:

    DIGITAL_PIN_START = 2  # Exclude pins 0 and 1 as they are used for USB serial comms

    def __init__(
        self,
        devices: ARDUINO_DEVICES_TYPE,
    ) -> None:
        self.pins = devices
