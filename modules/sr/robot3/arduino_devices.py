from __future__ import annotations

import abc
import enum
import random
import logging
from typing import Protocol

from controller import (
    LED,
    Robot,
    TouchSensor,
    DistanceSensor as WebotsDistanceSensor,
)
from sr.robot3.utils import map_to_range, get_robot_device
from sr.robot3.randomizer import add_jitter
from sr.robot3.output_frequency_limiter import OutputFrequencyLimiter

LOGGER = logging.getLogger(__name__)


class GPIOPinMode(str, enum.Enum):
    """The possible modes for a GPIO pin."""
    INPUT = 'INPUT'
    INPUT_PULLUP = 'INPUT_PULLUP'
    OUTPUT = 'OUTPUT'


DIGITAL_READ_MODES = {GPIOPinMode.INPUT, GPIOPinMode.INPUT_PULLUP, GPIOPinMode.OUTPUT}
DIGITAL_WRITE_MODES = {GPIOPinMode.OUTPUT}
ANALOG_READ_MODES = {GPIOPinMode.INPUT}


class Device(Protocol):
    def analogue_read(self) -> float:
        ...

    def digital_write(self, value: bool) -> None:
        ...


class Pin(abc.ABC):
    """
    A device connected to a pin on the Arduino.
    """
    _ANALOGUE_RANGE = (0., 5.)  # Volts

    def __init__(
        self,
        supports_analogue: bool,
        index: int,
        device: Device,
        disabled: bool = False,
    ) -> None:
        """
        :param supports_analogue: Whether the pin supports analogue reads.
        :param disabled: Whether the pin can be controlled.
        """
        self._supports_analogue = supports_analogue
        self._index = index
        self._device = device
        self._disabled = disabled
        self._mode = GPIOPinMode.INPUT

    def _check_if_disabled(self) -> None:
        if self._disabled:
            raise IOError('This pin cannot be controlled.')

    @property
    def mode(self) -> GPIOPinMode:
        """
        Get the mode of the pin.

        This returns the cached value since the board does not report this.

        :raises IOError: If this pin cannot be controlled.
        :return: The mode of the pin.
        """
        self._check_if_disabled()
        return self._mode

    @mode.setter
    def mode(self, value: GPIOPinMode) -> None:
        """
        Set the mode of the pin.

        To do analogue or digital reads set the mode to INPUT or INPUT_PULLUP.
        To do digital writes set the mode to OUTPUT.

        :param value: The mode to set the pin to.
        :raises IOError: If the pin mode is not a GPIOPinMode.
        :raises IOError: If this pin cannot be controlled.
        """
        self._check_if_disabled()
        if not isinstance(value, GPIOPinMode):
            raise IOError('Pin mode only supports being set to a GPIOPinMode')

        self._mode = value

    def digital_read(self) -> bool:
        """
        Perform a digital read on the pin.

        :raises IOError: If the pin's current mode does not support digital read
        :raises IOError: If this pin cannot be controlled.
        :return: The digital value of the pin.
        """
        self._check_if_disabled()
        if self.mode not in DIGITAL_READ_MODES:
            raise IOError(f'Digital read is not supported in {self.mode}')

        # Emulate reading an analogue signal and interpreting as a digital one.
        return self._device.analogue_read() > 1

    def digital_write(self, value: bool) -> None:
        """
        Write a digital value to the pin.

        :param value: The value to write to the pin.
        :raises IOError: If the pin's current mode does not support digital write.
        :raises IOError: If this pin cannot be controlled.
        """
        self._check_if_disabled()
        if self.mode not in DIGITAL_WRITE_MODES:
            raise IOError(f'Digital write is not supported in {self.mode}')

        self._device.digital_write(value)

    def analog_read(self) -> float:
        """
        Get the analogue voltage on the pin.

        This is returned in volts. Only pins A0-A7 support analogue reads.

        :raises IOError: If the pin or its current mode does not support analogue read.
        :raises IOError: If this pin cannot be controlled.
        :return: The analogue voltage on the pin, ranges from 0 to 5.
        """
        self._check_if_disabled()
        if self.mode not in ANALOG_READ_MODES:
            raise IOError(f'Analogue read is not supported in {self.mode}')
        if not self._supports_analogue:
            raise IOError('Pin does not support analogue read')

        return add_jitter(self._device.analogue_read(), *self._ANALOGUE_RANGE)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__qualname__} "
            f"index={self._index} "
            f"analogue={self._supports_analogue} "
            f"disabled={self._disabled}>"
        )


class NullDevice(Device):
    def analogue_read(self) -> float:
        return map_to_range(0, 1, *Pin._ANALOGUE_RANGE, random.random())

    def digital_write(self, value: bool) -> None:
        pass


class DisabledPin(Pin):
    def __init__(self, index: int, supports_analogue: bool = False) -> None:
        super().__init__(supports_analogue, index, device=NullDevice(), disabled=True)


class DistanceSensor(Device):
    """
    A standard Webots distance sensor, adapted to being a voltage based arduino sensor.
    """

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = get_robot_device(webot, sensor_name, WebotsDistanceSensor)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def analogue_read(self) -> float:
        return map_to_range(
            self.webot_sensor.getMinValue(),
            self.webot_sensor.getMaxValue(),
            *Pin._ANALOGUE_RANGE,
            self.webot_sensor.getValue(),
        )


class PressureSensor(Device):
    """
    A Webots touch sensor with pressure, adapted to being a voltage based arduino sensor.
    """

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = get_robot_device(webot, sensor_name, TouchSensor)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def analogue_read(self) -> float:
        # Currently we only the return Z-axis force.
        return self.webot_sensor.getValues()[2] / 100


class Microswitch(Device):
    """
    A standard Webots touch sensor.
    """

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = get_robot_device(webot, sensor_name, TouchSensor)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def analogue_read(self) -> float:
        return Pin._ANALOGUE_RANGE[int(self._digital_read())]

    def _digital_read(self) -> bool:
        """
        Returns whether or not the touch sensor is in contact with something.
        """
        return self.webot_sensor.getValue() > 0


class Led(Device):
    """
    A standard Webots LED.
    The value is a boolean to switch the LED on (True) or off (False).
    """

    def __init__(
        self,
        webot: Robot,
        device_name: str,
        limiter: OutputFrequencyLimiter,
        pin_num: int,
    ) -> None:
        self.webot_sensor = get_robot_device(webot, device_name, LED)
        self._limiter = limiter
        self._pin_num = pin_num

    def digital_write(self, value: bool) -> None:
        if not self._limiter.can_change():
            LOGGER.warning(
                "Rate limited change to LED output (requested setting LED on pin %d to %r)",
                self._pin_num,
                value,
            )
            return

        self.webot_sensor.set(value)
