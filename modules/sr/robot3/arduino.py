"""The Arduino module provides an interface to the simulated Arduino."""
from __future__ import annotations

from enum import Enum, IntEnum
from types import MappingProxyType
from typing import Dict

from controller import Robot
from sr.robot3.utils import BoardIdentity
from sr.robot3.arduino_devices import (
    Led,
    EmptyPin,
    PinDevice,
    Microswitch,
    DistanceSensor,
    PressureSensor,
)


class GPIOPinMode(str, Enum):
    """The possible modes for a GPIO pin."""
    INPUT = 'INPUT'
    INPUT_PULLUP = 'INPUT_PULLUP'
    OUTPUT = 'OUTPUT'


class AnalogPins(IntEnum):
    """The analog pins on the Arduino."""
    A0 = 14
    A1 = 15
    A2 = 16
    A3 = 17
    A4 = 18
    A5 = 19

    # Note: these pins don't exist on a real arduino.
    A6 = 20
    A7 = 21


DIGITAL_READ_MODES = {GPIOPinMode.INPUT, GPIOPinMode.INPUT_PULLUP, GPIOPinMode.OUTPUT}
DIGITAL_WRITE_MODES = {GPIOPinMode.OUTPUT}
ANALOG_READ_MODES = {GPIOPinMode.INPUT}


def init_arduinos(webot: Robot) -> MappingProxyType[str, Arduino]:
    serial_number = '1234567890'

    # NOTE: the names here correspond to the names given to devices in Webots
    # and, in some places, the keyboard controller.
    pin_devices = {
        2: Microswitch(webot, 'back bump sensor'),
        3: Led(webot, 'led 1', pin_num=3),
        4: Led(webot, 'led 2', pin_num=4),
        AnalogPins.A0: DistanceSensor(webot, 'Front Left DS'),
        AnalogPins.A1: DistanceSensor(webot, 'Front Right DS'),
        AnalogPins.A2: DistanceSensor(webot, 'Left DS'),
        AnalogPins.A3: DistanceSensor(webot, 'Right DS'),
        AnalogPins.A4: DistanceSensor(webot, 'Front DS'),
        AnalogPins.A5: DistanceSensor(webot, 'Back DS'),
        # NOTE: these pins don't exist on a real arduino.
        AnalogPins.A6: PressureSensor(webot, 'finger pressure left'),
        AnalogPins.A7: PressureSensor(webot, 'finger pressure right'),
    }

    return MappingProxyType({
        serial_number: Arduino(webot, serial_number, devices=pin_devices),
    })


class Arduino:
    """
    The Arduino board interface.

    This is intended to be used with Arduino Uno boards running the sbot firmware.

    :param webot: The robot object to connect to devices on.
    :param serial_number: The serial number of the board.
    :param devices: The devices connected to the board, a collection of PinDevices.
    """
    __slots__ = ('_serial_num', '_serial', '_pins', '_identity')

    @staticmethod
    def get_board_type() -> str:
        """
        Return the type of the board.

        :return: The literal string 'Arduino'.
        """
        return 'Arduino'

    def __init__(
        self,
        webot: Robot,
        serial_number: str,
        devices: Dict[int, PinDevice],
    ) -> None:
        # Stored for use in the identify method and repr.
        self._serial_num = serial_number

        self._pins = (
            # Pins 0 and 1 are reserved for serial comms
            Pin(0, supports_analog=False, disabled=True),
            Pin(1, supports_analog=False, disabled=True),
            # splat in both the digital and analog pins
            *(Pin(index, supports_analog=False) for index in range(2, 14)),
            *(Pin(index, supports_analog=True) for index in AnalogPins),
        )

        # Connect the devices to the pins.
        for pin_num, pin_device in devices.items():
            self._pins[pin_num]._connect_device(pin_device)

    def identify(self) -> BoardIdentity:
        """
        Get the identity of the board.

        The asset tag of the board is the serial number.

        :return: The identity of the board.
        """

        return BoardIdentity(
            manufacturer="Student Robotics",
            board_type="SRduino",
            asset_tag=self._serial_num,
            sw_version='1.0',
        )

    @property
    def pins(self) -> tuple[Pin, ...]:
        """
        The pins on the Arduino.

        :return: A tuple of the pins on the Arduino.
        """
        return self._pins

    def command(self, command: str) -> str:
        """
        Send a command to the board.
        NOTE This is currently not implemented in the simulator.

        :param command: The command to send to the board.
        :return: The response from the board.
        """
        return ''

    def map_pin_number(self, pin_number: int) -> str:
        """
        Map the pin number to the the serial format.
        Pin numbers are sent as printable ASCII characters, with 0 being 'a'.

        :param pin_number: The pin number to encode.
        :return: The pin number in the serial format.
        :raises ValueError: If the pin number is invalid.
        """
        try:  # bounds check
            self.pins[pin_number]._check_if_disabled()
        except (IndexError, IOError):
            raise ValueError("Invalid pin provided") from None
        return chr(pin_number + ord('a'))

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial_num}>"


class Pin:
    """
    A pin on the Arduino.

    :param index: The index of the pin.
    :param supports_analog: Whether the pin supports analog reads.
    :param disabled: Whether the pin can be controlled.
    """
    __slots__ = ('_device', '_index', '_supports_analog', '_disabled', '_mode')

    def __init__(
        self,
        index: int,
        supports_analog: bool,
        disabled: bool = False,
    ):
        self._index = index
        self._supports_analog = supports_analog
        self._disabled = disabled
        self._mode = GPIOPinMode.INPUT

        # The device is set to an empty pin by default.
        self._device: PinDevice = EmptyPin()

    def _connect_device(self, device: PinDevice) -> None:
        """
        Connect a device to the pin.

        :param device: The device wrapper to use to control a device in webots.
        """
        self._device = device

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

        To do analog or digital reads set the mode to INPUT or INPUT_PULLUP.
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

        return self._device.digital_read()

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
        Get the analog voltage on the pin.

        This is returned in volts. Only pins A0-A5 support analog reads.

        :raises IOError: If the pin or its current mode does not support analog read.
        :raises IOError: If this pin cannot be controlled.
        :return: The analog voltage on the pin, ranges from 0 to 5.
        """
        self._check_if_disabled()
        if self.mode not in ANALOG_READ_MODES:
            raise IOError(f'Analog read is not supported in {self.mode}')
        if not self._supports_analog:
            raise IOError('Pin does not support analog read')

        return self._device.analog_read()

    def _check_if_disabled(self) -> None:
        """
        Check if the pin is disabled.

        :raises IOError: If the pin is disabled.
        """
        if self._disabled:
            raise IOError('This pin cannot be controlled.')

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__qualname__} "
            f"index={self._index} analog={self._supports_analog} "
            f"disabled={self._disabled} {self._device!r}>"
        )
