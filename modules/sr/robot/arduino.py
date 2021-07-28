from __future__ import annotations

from enum import Enum
from typing import List, Dict

from controller import Robot
from shared_utils import RobotType
from sr.robot.arduino_devices import Led, Microswitch, DistanceSensor
from sr.robot.output_frequency_limiter import OutputFrequencyLimiter


class AnaloguePin(Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"


def init_arduino_array(webot: Robot, robot_type: RobotType) -> List[Arduino]:
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
        # TODO: placeholder crane ruggeduino
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

    analouge_sensors = [
        DistanceSensor(webot, name)
        for name in dist_sensor_names
    ]
    analogue_input_dict = {key: sensor for key, sensor in zip(
        analouge_sensors,
        AnaloguePin,
    )}

    digital_sensors = [
        Microswitch(webot, name)
        for name in switch_names
    ]
    digital_input_dict = {index: sensor for index, sensor in enumerate(
        digital_sensors,
    )}

    limiter = OutputFrequencyLimiter(webot)
    digital_outputs = [
        Led(webot, name, limiter, pin)
        for pin, name in enumerate(
            led_names,
            start=Arduino.DIGITAL_PIN_START + len(digital_input_dict),
        )
    ]

    digital_output_dict = {index: output for index, output in enumerate(
        digital_outputs,
        start=Arduino.DIGITAL_PIN_START + len(digital_input_dict),
    )}

    return [Arduino({
        **analogue_input_dict,
        **digital_input_dict,
        **digital_output_dict,
    })]


class Arduino:

    DIGITAL_PIN_START = 2  # Exclude pins 0 and 1 as they are used for USB serial comms

    def __init__(
        self,
        devices: Dict
    ) -> None:
        self.pins = devices

    # pin_mode not present as the pins have fixed behaviours
    # in the simulator.
