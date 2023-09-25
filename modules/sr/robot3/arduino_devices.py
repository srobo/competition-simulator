from __future__ import annotations

import logging
from collections.abc import Iterable

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


class ArduinoDevice:
    def analogue_read(self) -> float:
        raise NotImplementedError()

    def digital_read(self) -> bool:
        raise NotImplementedError()

    def digital_write(self, value: bool) -> None:
        raise NotImplementedError()


class DistanceSensor(ArduinoDevice):
    """
    A standard Webots distance sensor,  we convert the distance to metres.
    """

    LOWER_BOUND = 0
    UPPER_BOUND = 2

    @classmethod
    def many(cls, webot: Robot, sensor_names: Iterable[str]) -> list[DistanceSensor]:
        return [cls(webot, x) for x in sensor_names]

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = get_robot_device(webot, sensor_name, WebotsDistanceSensor)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def __get_scaled_distance(self) -> float:
        return map_to_range(
            self.webot_sensor.getMinValue(),
            self.webot_sensor.getMaxValue(),
            DistanceSensor.LOWER_BOUND,
            DistanceSensor.UPPER_BOUND,
            self.webot_sensor.getValue(),
        )

    def analogue_read(self) -> float:
        """
        Returns the distance measured by the sensor, in metres.
        """
        return add_jitter(
            self.__get_scaled_distance(),
            DistanceSensor.LOWER_BOUND,
            DistanceSensor.UPPER_BOUND,
        )


class PressureSensor(ArduinoDevice):
    """
    A Webots touch sensor with pressure,  we convert the distance to metres.
    """

    LOWER_BOUND = 0
    UPPER_BOUND = 3

    @classmethod
    def many(cls, webot: Robot, sensor_names: Iterable[str]) -> list[PressureSensor]:
        return [cls(webot, x) for x in sensor_names]

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = get_robot_device(webot, sensor_name, TouchSensor)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def __get_pressure(self) -> float:
        # Currently we only the return Z-axis force.
        return self.webot_sensor.getValues()[2] / 100

    def analogue_read(self) -> float:
        """
        Returns the distance measured by the sensor, in metres.
        """
        return add_jitter(
            self.__get_pressure(),
            PressureSensor.LOWER_BOUND,
            PressureSensor.UPPER_BOUND,
        )


class Microswitch(ArduinoDevice):
    """
    A standard Webots touch sensor.
    """

    @classmethod
    def many(cls, webot: Robot, sensor_names: Iterable[str]) -> list[Microswitch]:
        return [cls(webot, x) for x in sensor_names]

    def __init__(self, webot: Robot, sensor_name: str) -> None:
        self.webot_sensor = get_robot_device(webot, sensor_name, TouchSensor)
        self.webot_sensor.enable(int(webot.getBasicTimeStep()))

    def digital_read(self) -> bool:
        """
        Returns whether or not the touch sensor is in contact with something.
        """
        return self.webot_sensor.getValue() > 0


class Led(ArduinoDevice):
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
