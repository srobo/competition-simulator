from typing import Optional

from controller import (
    LED,
    Motor,
    Robot,
    Emitter,
    Receiver,
    TouchSensor,
    DistanceSensor,
)


def map_to_range(
    old_min: float,
    old_max: float,
    new_min: float,
    new_max: float,
    value: float,
) -> float:
    """Maps a value from within one range of inputs to within a range of outputs."""
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min


def get_robot_emitter(robot: Robot, device: str) -> Emitter:
    try:
        # webots 2020b fails to assign the output to the expected type
        emitter: Optional[Emitter] = robot.getDevice(device)
        # webots 2020b always returns None when not raising TypeError
        if emitter is None:
            raise TypeError
    except TypeError:
        emitter = robot.getEmitter(device)
    return emitter


def get_robot_receiver(robot: Robot, device: str) -> Receiver:
    try:
        # webots 2020b fails to assign the output to the expected type
        receiver: Optional[Receiver] = robot.getDevice(device)
        # webots 2020b always returns None when not raising TypeError
        if receiver is None:
            raise TypeError
    except TypeError:
        receiver = robot.getReceiver(device)
    return receiver


def get_robot_motor(robot: Robot, device: str) -> Motor:
    try:
        # webots 2020b fails to assign the output to the expected type
        motor: Optional[Motor] = robot.getDevice(device)
        # webots 2020b always returns None when not raising TypeError
        if motor is None:
            raise TypeError
    except TypeError:
        motor = robot.getMotor(device)
    return motor


def get_robot_LED(robot: Robot, device: str) -> LED:
    try:
        # webots 2020b fails to assign the output to the expected type
        led: Optional[LED] = robot.getDevice(device)
        # webots 2020b always returns None when not raising TypeError
        if led is None:
            raise TypeError
    except TypeError:
        led = robot.getLED(device)
    return led


def get_robot_distance_sensor(robot: Robot, device: str) -> DistanceSensor:
    try:
        # webots 2020b fails to assign the output to the expected type
        distance_sensor: Optional[DistanceSensor] = robot.getDevice(device)
        # webots 2020b always returns None when not raising TypeError
        if distance_sensor is None:
            raise TypeError
    except TypeError:
        distance_sensor = robot.getDistanceSensor(device)
    return distance_sensor


def get_robot_touch_sensor(robot: Robot, device: str) -> TouchSensor:
    try:
        # webots 2020b fails to assign the output to the expected type
        touch_Sensor: Optional[TouchSensor] = robot.getDevice(device)
        # webots 2020b always returns None when not raising TypeError
        if touch_Sensor is None:
            raise TypeError
    except TypeError:
        touch_Sensor = robot.getTouchSensor(device)
    return touch_Sensor
