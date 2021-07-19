from typing import List

from controller import Robot
from shared_utils import RobotType
from sr.robot.ruggeduino_devices import Led, Microswitch, DistanceSensor
from sr.robot.output_frequency_limiter import OutputFrequencyLimiter


def init_ruggeduino_array(webot: Robot, robot_type: RobotType) -> 'List[Ruggeduino]':
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

    analogue_input_array = [DistanceSensor(webot, name) for name in dist_sensor_names]

    digital_input_array = [Microswitch(webot, name) for name in switch_names]

    limiter = OutputFrequencyLimiter(webot)
    digital_output_array = [
        Led(webot, name, limiter, pin)
        for pin, name in enumerate(
            led_names,
            start=Ruggeduino.DIGITAL_PIN_START + len(digital_input_array),
        )
    ]

    return [Ruggeduino(analogue_input_array, digital_input_array, digital_output_array)]


class Ruggeduino:

    DIGITAL_PIN_START = 2  # Exclude pins 0 and 1 as they are used for USB serial comms

    def __init__(
        self,
        analogue_input_array: List[DistanceSensor],
        digital_input_array: List[Microswitch],
        digital_output_array: List[Led],
    ) -> None:
        self.analogue_input_array = analogue_input_array
        self.digital_input_array = digital_input_array
        self.digital_output_array = digital_output_array

    def digital_read(self, pin: int) -> bool:
        """Read an digital input"""
        return self.digital_input_array[pin - Ruggeduino.DIGITAL_PIN_START].read_value()

    def digital_write(self, pin: int, level: bool) -> None:
        """Write a digital output"""
        array_index = pin - Ruggeduino.DIGITAL_PIN_START - len(self.digital_input_array)
        if array_index < 0:
            raise IndexError("Sorry pin %d can't be written to" % pin)
        return self.digital_output_array[array_index].write_value(level)

    def analogue_read(self, pin: int) -> float:
        """Read an analogue input"""
        return self.analogue_input_array[pin].read_value()

    # pin_mode not present as the pins have fixed behaviours
    # in the simulator.
