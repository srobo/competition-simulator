from __future__ import annotations

import os
import enum
import dataclasses
from pathlib import Path

_ETC_OS_RELEASE = Path('/etc/os-release')


class RobotMode(enum.Enum):
    # Note: The simulator internally continues to use the historical (lower
    # case) spelling of these modes, however for the competitor-facing API we
    # provide uppercased spellings to match sr.robot3.

    COMP = 'COMP'
    DEV = 'DEV'


@dataclasses.dataclass(frozen=True)
class Metadata:
    """Minimal version of robot metadata."""

    arena: str = 'A'
    zone: int = 0
    mode: RobotMode = RobotMode.DEV
    marker_offset: int = 0
    game_timeout: int | None = None
    wifi_enabled: bool = True

    # From Software
    astoria_version: str = ''
    kernel_version: str = ''
    arch: str = ''
    python_version: str = ''
    libc_ver: str = ''
    os_name: str | None = None
    os_pretty_name: str | None = None
    os_version: str | None = None

    # From robot settings file
    usercode_entrypoint: str = ''
    wifi_ssid: str | None = None
    wifi_psk: str | None = None
    wifi_region: str | None = None

    def is_wifi_valid(self) -> bool:
        return True

    @classmethod
    def get_os_version_info(cls, os_release_path: Path = _ETC_OS_RELEASE) -> dict[str, str]:
        return {}


def init_metadata() -> tuple[Metadata, Path]:
    mode_str = os.environ.get('SR_ROBOT_MODE', 'dev').upper()

    zone_str = os.environ.get('SR_ROBOT_ZONE', '0')
    zone = int(zone_str)
    if zone not in range(4):
        raise ValueError(f"Zone must be in range 0-3 inclusive. {zone_str!r} is invalid")

    return (
        Metadata(mode=RobotMode(mode_str), zone=zone),
        Path(os.environ['SR_ROBOT_FILE']).parent.absolute(),
    )
