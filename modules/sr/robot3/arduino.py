from __future__ import annotations

import enum
import functools
from collections.abc import Mapping

from controller import Robot
from sr.robot3.arduino_devices import (
    Led,
    Pin,
    Device,
    NullDevice,
    DisabledPin,
    Microswitch,
    DistanceSensor,
    PressureSensor,
)
from sr.robot3.output_frequency_limiter import OutputFrequencyLimiter


class AnaloguePin(enum.IntEnum):
    """The analogue pins on the Arduino."""
    A0 = 14
    A1 = 15
    A2 = 16
    A3 = 17
    A4 = 18
    A5 = 19

    # Note: these pins don't exist on a real arduino.
    A6 = 20
    A7 = 21


def init_arduinos(webot: Robot) -> dict[str, Arduino]:
    # Apply common arguments upfront to simplify later declarations.
    _DistanceSensor = functools.partial(DistanceSensor, webot)
    _PressureSensor = functools.partial(PressureSensor, webot)
    _Microswitch = functools.partial(Microswitch, webot)
    _Led = functools.partial(Led, webot, limiter=OutputFrequencyLimiter(webot))

    # Explicitly list pin mappings for easier maintenance and alignment with the
    # docs.
    #
    # Note: the names here correspond to the names given to devices in Webots
    # and, in some places, the keyboard controller.
    devices = {
        2: _Microswitch('back bump sensor'),
        3: _Led('led 1', pin_num=3),
        4: _Led('led 2', pin_num=4),

        AnaloguePin.A0: _DistanceSensor('Front Left DS'),
        AnaloguePin.A1: _DistanceSensor('Front Right DS'),
        AnaloguePin.A2: _DistanceSensor('Left DS'),
        AnaloguePin.A3: _DistanceSensor('Right DS'),
        AnaloguePin.A4: _DistanceSensor('Front DS'),
        AnaloguePin.A5: _DistanceSensor('Back DS'),

        # Note: these pins don't exist on a real arduino.
        AnaloguePin.A6: _PressureSensor('finger pressure left'),
        AnaloguePin.A7: _PressureSensor('finger pressure right'),
    }

    return {
        '1234567890': Arduino(devices),
    }


class Arduino:
    # Pins 0 & 1 are reserved for USB comms, inserted as DisabledPins in __init__.
    # Arduinos normally have 20 pins, however we cheat a bit and allow for a few
    # more analogue pins than strictly exist.
    _VALID_PINS = range(2, max(20, max(AnaloguePin) + 1))
    _ANALOGUE_PINS = list(AnaloguePin)

    def __init__(self, devices: Mapping[int, Device]) -> None:
        invalid_pins = [x for x in devices.keys() if x not in self._VALID_PINS]
        if invalid_pins:
            raise ValueError(f"Invalid pins: {invalid_pins}")

        def get_pin(index: int) -> Pin:
            supports_analogue = index in self._ANALOGUE_PINS

            device = devices.get(index)
            if not device:
                device = NullDevice()

            return Pin(supports_analogue, device)

        self.pins: tuple[Pin, ...] = (
            DisabledPin(),
            DisabledPin(),
            *(get_pin(x) for x in self._VALID_PINS),
        )
