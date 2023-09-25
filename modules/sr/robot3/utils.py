from __future__ import annotations

from typing import TypeVar, NamedTuple

from controller import Robot
from controller.device import Device

TDevice = TypeVar('TDevice', bound=Device)


class BoardIdentity(NamedTuple):
    """
    A container for the identity of a board.

    All the board firmwares should return this information in response to
    the *IDN? query.

    :param manufacturer: The manufacturer of the board
    :param board_type: The short name of the board, i.e. PBv4B
    :param asset_tag: The asset tag of the board,
        this should match what is printed on the board
    :param sw_version: The firmware version of the board
    """
    manufacturer: str = ""
    board_type: str = ""
    asset_tag: str = ""
    sw_version: str = ""


def map_to_range(
    old_min: float,
    old_max: float,
    new_min: float,
    new_max: float,
    value: float,
) -> float:
    """Maps a value from within one range of inputs to within a range of outputs."""
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min


def maybe_get_robot_device(robot: Robot, name: str, kind: type[TDevice]) -> TDevice | None:
    device = robot.getDevice(name)
    if device is None:
        return None
    if not isinstance(device, kind):
        raise TypeError
    return device


def get_robot_device(robot: Robot, name: str, kind: type[TDevice]) -> TDevice:
    device = robot.getDevice(name)
    if not isinstance(device, kind):
        raise TypeError
    return device
