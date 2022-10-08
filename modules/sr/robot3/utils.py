from __future__ import annotations

from typing import Type, TypeVar

from controller import Robot, Device

TDevice = TypeVar('TDevice', bound=Device)


def map_to_range(
    old_min: float,
    old_max: float,
    new_min: float,
    new_max: float,
    value: float,
) -> float:
    """Maps a value from within one range of inputs to within a range of outputs."""
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min


def get_robot_device(robot: Robot, name: str, kind: Type[TDevice]) -> TDevice:
    device = robot.getDevice(name)
    if not isinstance(device, kind):
        raise TypeError
    return device
