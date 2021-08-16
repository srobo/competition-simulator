from __future__ import annotations

from enum import Enum
from typing import Dict, List, Union

from controller import Robot
from shared_utils import RobotType
from sbot.arduino_devices import Led, Microswitch, DistanceSensor
from sbot.output_frequency_limiter import OutputFrequencyLimiter


class AnaloguePin(Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"


ARDUINO_DEVICES_TYPE = Dict[Union[AnaloguePin, int], Union[DistanceSensor, Microswitch, Led]]


def init_arduino(webot: Robot, robot_type: RobotType) -> Arduino:
    led_names: List[str]

    # The names in these arrays correspond to the names given to devices in Webots
    if robot_type == RobotType.FORKLIFT:
        dist_sensor_names = [
            # Updating these? Also update controllers/example_controller/keyboard_controller.py
            "Front Left DS",
            "Front Right DS",
            "Left DS",
            "Right DS",
            "Front DS",
            "Back DS",
        ]
        switch_names = [
            # "front bump sensor",
            "back bump sensor",
        ]
        led_names = [
            # "led 1",
            # "led 2",
            # "led 3",
            # "led 4",
            # "led 5",
            # "led 6",
        ]
    else:
        dist_sensor_names = ["Hook DS"]
        switch_names = []
        led_names = []

    analouge_sensors = [
        DistanceSensor(webot, name)
        for name in dist_sensor_names
    ]
    analogue_input_dict: ARDUINO_DEVICES_TYPE = {key: sensor for key, sensor in zip(
        AnaloguePin,
        analouge_sensors,
    )}

    digital_sensors = [
        Microswitch(webot, name)
        for name in switch_names
    ]
    digital_input_dict: ARDUINO_DEVICES_TYPE = {index: sensor for index, sensor in enumerate(
        digital_sensors,
        start=Arduino.DIGITAL_PIN_START,
    )}

    limiter = OutputFrequencyLimiter(webot)
    digital_outputs = [
        Led(webot, name, limiter, pin)
        for pin, name in enumerate(
            led_names,
            start=Arduino.DIGITAL_PIN_START + len(digital_input_dict),
        )
    ]

    digital_output_dict: ARDUINO_DEVICES_TYPE = {index: output for index, output in enumerate(
        digital_outputs,
        start=Arduino.DIGITAL_PIN_START + len(digital_input_dict),
    )}

    return Arduino({
        **analogue_input_dict,
        **digital_input_dict,
        **digital_output_dict,
    })


class Arduino:

    DIGITAL_PIN_START = 2  # Exclude pins 0 and 1 as they are used for USB serial comms

    def __init__(
        self,
        devices: ARDUINO_DEVICES_TYPE,
    ) -> None:
        self.pins = devices

    # pin_mode not present as the pins have fixed behaviours
    # in the simulator.
