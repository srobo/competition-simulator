from typing import cast, Type, TypeVar, Optional

from controller import (
    LED,
    Motor,
    Robot,
    Device,
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


TDevice = TypeVar('TDevice', bound=Device)


def get_robot_device(robot: Robot, name: str, kind: Type[TDevice]) -> TDevice:
    device: Optional[Device] = None
    try:  # webots 2020b fails to assign the output to the expected type raising TypeError
        device = robot.getDevice(name)
    except TypeError:
        pass
    if device is None:  # webots 2020b always returns None when not raising TypeError
        if kind is Emitter:
            device = robot.getEmitter(name)
        elif kind is Receiver:
            device = robot.getReceiver(name)
        elif kind is Motor:
            device = robot.getMotor(name)
        elif kind is LED:
            device = robot.getLED(name)
        elif kind is DistanceSensor:
            device = robot.getDistanceSensor(name)
        elif kind is TouchSensor:
            device = robot.getTouchSensor(name)
    if not isinstance(device, kind):
        raise TypeError
    return cast(TDevice, device)
