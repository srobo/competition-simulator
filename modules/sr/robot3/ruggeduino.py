from __future__ import annotations

from enum import IntEnum
from typing import Dict, Union

from controller import Robot
from sr.robot3.ruggeduino_devices import (
    Led,
    Microswitch,
    DistanceSensor,
    PressureSensor,
    RuggeduinoDevice,
)
from sr.robot3.output_frequency_limiter import OutputFrequencyLimiter


class GPIOPinMode(IntEnum):
    """Hardware modes that a GPIO pin can be set to."""

    DIGITAL_INPUT = 0  #: The digital state of the pin can be read
    DIGITAL_INPUT_PULLUP = 1  #: Same as DIGITAL_INPUT but internal pull-up is enabled
    DIGITAL_INPUT_PULLDOWN = 2  #: Same as DIGITAL_INPUT but internal pull-down is enabled
    DIGITAL_OUTPUT = 3  #: The digital state of the pin can be set.

    ANALOGUE_INPUT = 4  #: The analogue voltage of the pin can be read.
    ANALOGUE_OUTPUT = 5  #: The analogue voltage of the pin can be set using a DAC.

    PWM_OUTPUT = 6  #: A PWM output signal can be created on the pin.


class AnaloguePin(IntEnum):
    A0 = 14
    A1 = 15
    A2 = 16
    A3 = 17
    A4 = 18
    A5 = 19
    A6 = 20


DevicesMapping = Dict[Union[AnaloguePin, int], RuggeduinoDevice]


def init_ruggeduino_array(webot: Robot) -> dict[str, Ruggeduino]:
    # The names in these arrays correspond to the names given to devices in Webots

    dist_sensor_names = [
        # Updating these? Also update controllers/example_controller/keyboard_controller.py
        "Front Left DS",
        "Front Right DS",
        "Left DS",
        "Right DS",
        "Front DS",
        "Back DS",
    ]
    pressure_sensor_names = [
        "finger pressure",
    ]
    switch_names = [
        "back bump sensor",
    ]
    led_names = [
        "led 1",
        "led 2",
    ]

    analogue_sensors = [
        DistanceSensor(webot, name)
        for name in dist_sensor_names
    ] + [
        PressureSensor(webot, name)
        for name in pressure_sensor_names
    ]

    analogue_input_dict: DevicesMapping = {
        key: sensor
        for key, sensor in zip(AnaloguePin, analogue_sensors)
    }

    digital_sensors = [
        Microswitch(webot, name)
        for name in switch_names
    ]
    digital_input_dict: DevicesMapping = {
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

    digital_output_dict: DevicesMapping = {
        index: output
        for index, output in enumerate(
            digital_outputs,
            start=Ruggeduino.DIGITAL_PIN_START + len(digital_input_dict),
        )
    }

    return {
        '1234567890': Ruggeduino({
            **analogue_input_dict,
            **digital_input_dict,
            **digital_output_dict,
        }),
    }


class Ruggeduino:

    DIGITAL_PIN_START = 2  # Exclude pins 0 and 1 as they are used for USB serial comms

    def __init__(
        self,
        devices: DevicesMapping,
    ) -> None:
        self.pins = devices
