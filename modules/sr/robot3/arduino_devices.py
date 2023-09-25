from __future__ import annotations

import logging
from typing import Optional

from controller import (
    LED,
    Robot,
    TouchSensor,
    DistanceSensor as WebotsDistanceSensor,
)
from sr.robot3.utils import map_to_range, get_robot_device
from controller.device import Device
from sr.robot3.randomizer import add_jitter
from sr.robot3.output_frequency_limiter import OutputFrequencyLimiter

LOGGER = logging.getLogger(__name__)


class PinDevice:
    """
    A device connected to a pin on the Arduino.
    """
    _ANALOG_MIN = 0.0  # Volts
    _ANALOG_MAX = 5.0
    _DEVICE_TYPE: Optional[type[Device]] = None
    _webot_device: Optional[Device]

    def __init__(
        self,
        webot: Robot,
        device_name: str,
    ) -> None:
        """
        :param webot: The robot object to connect to devices on.
        :param device_name: The identifier of the device on the robot.
        """
        self._webot_device: Device
        self._device_name = device_name
        if self._DEVICE_TYPE is not None:
            self._webot_device = get_robot_device(webot, device_name, self._DEVICE_TYPE)
            timestep = int(webot.getBasicTimeStep())
            if hasattr(self._webot_device, "enable"):
                # Only the sensor devices have an enable method.
                self._webot_device.enable(timestep)

    @classmethod
    def empty(cls) -> PinDevice:
        """
        Returns a PinDevice that does nothing.

        This is useful for when a device is not connected to a pin.
        Since there is no device, the robot object is nulled out.
        """
        if cls._DEVICE_TYPE is not None:
            raise ValueError("An empty PinDevice is only available on the base class")
        return cls(None, "")  # type: ignore[arg-type]

    def digital_read(self) -> bool:
        return False

    def digital_write(self, value: bool) -> None:
        return

    def analog_read(self) -> float:
        return 0.0

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__qualname__} "
            f"device={self._device_name}>"
        )


class DistanceSensor(PinDevice):
    """
    A standard Webots distance sensor, adapted to being a voltage based arduino sensor.

    With the current distance sensors the output is 2.5 V/m
    """
    _DEVICE_TYPE = WebotsDistanceSensor
    _webot_device: WebotsDistanceSensor

    def analog_read(self) -> float:
        raw_value = map_to_range(
            self._webot_device.getMinValue(),
            self._webot_device.getMaxValue(),
            self._ANALOG_MIN,
            self._ANALOG_MAX,
            self._webot_device.getValue(),
        )
        return add_jitter(raw_value, self._ANALOG_MIN, self._ANALOG_MAX)


class PressureSensor(PinDevice):
    """
    A Webots touch sensor with pressure, adapted to being a voltage based arduino sensor.

    Range is approximately 0.0-3.0V.
    """
    _DEVICE_TYPE = TouchSensor
    _webot_device: TouchSensor

    def analog_read(self) -> float:
        # Currently we only the return Z-axis force.
        raw_value = self._webot_device.getValues()[2] / 100
        return add_jitter(raw_value, self._ANALOG_MIN, self._ANALOG_MAX)


class Microswitch(PinDevice):
    """
    A standard Webots touch sensor.
    """
    _DEVICE_TYPE = TouchSensor
    _webot_device: TouchSensor

    def digital_read(self) -> bool:
        """
        Returns whether or not the touch sensor is in contact with something.
        """
        return self._webot_device.getValue() > 0


class Led(PinDevice):
    """
    A standard Webots LED.
    The value is a boolean to switch the LED on (True) or off (False).
    """
    _DEVICE_TYPE = LED
    _webot_device: LED

    def __init__(
        self,
        webot: Robot,
        device_name: str,
        pin_num: int,
    ) -> None:
        super().__init__(webot, device_name)
        self._limiter = OutputFrequencyLimiter(webot)
        self._pin_num = pin_num

    def digital_write(self, value: bool) -> None:
        if not self._limiter.can_change():
            LOGGER.warning(
                "Rate limited change to LED output (requested setting LED on pin %d to %r)",
                self._pin_num,
                value,
            )
            return

        self._webot_device.set(value)
