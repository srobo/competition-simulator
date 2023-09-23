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
    A7 = 21


DevicesMapping = Dict[Union[AnaloguePin, int], RuggeduinoDevice]


def init_ruggeduinos(webot: Robot) -> dict[str, Ruggeduino]:
    # The names in these arrays correspond to the names given to devices in Webots

    analogue_inputs: list[RuggeduinoDevice] = []
    digital_inputs: list[RuggeduinoDevice] = []
    digital_outputs: dict[int, RuggeduinoDevice] = {}

    analogue_inputs += DistanceSensor.many(webot, [
        # Updating these? Also update controllers/example_controller/keyboard_controller.py
        "Front Left DS",
        "Front Right DS",
        "Left DS",
        "Right DS",
        "Front DS",
        "Back DS",
    ])
    analogue_inputs += PressureSensor.many(webot, [
        "finger pressure left",
        "finger pressure right",
    ])

    digital_inputs += Microswitch.many(webot, [
        "back bump sensor",
    ])

    led_names = [
        "led 1",
        "led 2",
    ]

    limiter = OutputFrequencyLimiter(webot)
    digital_outputs.update({
        pin: Led(webot, name, limiter, pin)
        for pin, name in enumerate(
            led_names,
            start=Ruggeduino.DIGITAL_PIN_START + len(digital_inputs),
        )
    })

    return {
        '1234567890': Ruggeduino({
            **dict(zip(AnaloguePin, analogue_inputs)),
            **dict(enumerate(digital_inputs, start=Ruggeduino.DIGITAL_PIN_START)),
            **digital_outputs,
        }),
    }


class Ruggeduino:

    DIGITAL_PIN_START = 2  # Exclude pins 0 and 1 as they are used for USB serial comms

    def __init__(
        self,
        devices: DevicesMapping,
    ) -> None:
        self.pins = devices
