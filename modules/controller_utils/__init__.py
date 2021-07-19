"""
Utilities for our controllers which relate to the running of matches.
"""

import os
import sys
import json
import datetime
from typing import IO, Dict, List, Optional, NamedTuple
from pathlib import Path

from shared_utils import RobotType

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Root directory of the specification of the Arena (and match)
ARENA_ROOT = Path(os.environ.get('ARENA_ROOT', REPO_ROOT.parent))

if not ARENA_ROOT.is_absolute():
    # It turns out that Webots sets the current directory of each controller to
    # the directory which contains the controller file. Since those are all
    # different, relative paths aren't meaningful.
    # Hint: `$PWD` or `%CD%` may be useful to construct an absolute path from
    # your relative path.
    raise ValueError(f"'ARENA_ROOT' must be an absolute path, got '{ARENA_ROOT}'")


NUM_ZONES = 2

GAME_DURATION_SECONDS = 120


class Resolution(NamedTuple):
    width: int
    height: int


class RecordingConfig(NamedTuple):
    resolution: Resolution
    quality: int


class MatchData(NamedTuple):
    match_number: int
    teams: List[Optional[str]]
    duration: int  # in seconds
    recording_config: Optional[RecordingConfig]


def get_mode_file() -> Path:
    """
    Returns the path to the mode file.

    Note: most consumers should not use this function, but rather should use
    other functions which return structure data which this file encodes.
    """
    return ARENA_ROOT / 'robot_mode.txt'


def get_match_file() -> Path:
    """
    Returns the path to the match file.

    Note: most consumers should not use this function, but rather should use
    other functions which return structure data which this file encodes.
    """
    return ARENA_ROOT / 'match.json'


def record_match_data(match_data: MatchData) -> None:
    # Use Proton format because it covers everything we need and already has a spec.
    data = {
        'match_number': match_data.match_number,
        'arena_id': 'Simulator',
        'teams': {
            tla: {'zone': idx}
            for idx, tla in enumerate(match_data.teams)
            if tla is not None
        },
        'duration': match_data.duration,
    }

    if match_data.recording_config:
        data['recording_config'] = {
            'resolution': match_data.recording_config.resolution._asdict(),
            'quality': match_data.recording_config.quality,
        }

    get_match_file().write_text(json.dumps(data, indent=4))


def record_arena_data(other_data: Dict[str, List[object]]) -> None:
    match_file = get_match_file()
    data = json.loads(match_file.read_text())
    arena_zones = data.setdefault('arena_zones', {})
    arena_zones['other'] = other_data.copy()
    arena_zones['other']['game_style'] = 'end_state'
    match_file.write_text(json.dumps(data, indent=4))


def read_match_data() -> MatchData:
    data = json.loads(get_match_file().read_text())

    tla_by_zone = {x['zone']: tla for tla, x in data['teams'].items()}
    tlas = [tla_by_zone.get(i) for i in range(NUM_ZONES)]

    if 'recording_config' in data:
        recording_config: Optional[RecordingConfig] = RecordingConfig(
            Resolution(**data['recording_config']['resolution']),
            data['recording_config']['quality'],
        )
    else:
        recording_config = None

    return MatchData(
        data['match_number'],
        tlas,
        data.get('duration', GAME_DURATION_SECONDS),
        recording_config,
    )


def get_match_duration_seconds() -> int:
    if get_match_file().exists():
        return read_match_data().duration
    return GAME_DURATION_SECONDS


def get_match_num() -> Optional[int]:
    if get_match_file().exists():
        return read_match_data().match_number
    return None


def get_recording_config() -> RecordingConfig:
    config = (
        read_match_data().recording_config
        if get_match_file().exists()
        else None
    )
    if config is None:
        config = RecordingConfig(
            Resolution(1920, 1080),
            quality=100,
        )
    return config


def get_recording_stem() -> Path:
    name: str = get_filename_safe_identifier()
    return ARENA_ROOT / 'recordings' / name


def get_filename_safe_identifier() -> str:
    """
    Return an identifier for the current run which is safe to use in filenames.

    This is of the form "match-{N}" during competition matches, or the current
    datetime in approximately ISO 8601 format otherwise.
    """

    match_num = get_match_num()
    if match_num is not None:
        return 'match-{}'.format(match_num)
    else:
        # Local time for convenience. We only care that this is a unique identifier.
        now = datetime.datetime.now()
        # Windows doesn't like colons in filenames.
        return now.isoformat().replace(':', '_')


def get_zone_robot_file_path(zone_id: int, robot_type: RobotType) -> Path:
    """
    Return the path to the robot.py for the given zone, without checking for
    existence.
    """
    return ARENA_ROOT / "zone-{}".format(zone_id) / "{}.py".format(robot_type.value)


def get_robot_log_filename(zone_id: int, robot_type: RobotType) -> str:
    identifier = get_filename_safe_identifier()
    return f'log-zone-{zone_id}-{robot_type.value}-{identifier}.txt'


def get_competition_supervisor_log_filepath() -> Path:
    identifier = get_filename_safe_identifier()
    return ARENA_ROOT / f'supervisor-log-{identifier}.txt'


def get_robot_mode() -> str:
    mode_file = get_mode_file()
    if not mode_file.exists():
        return "dev"
    return mode_file.read_text().strip()


class SimpleTee:
    """
    Forwards calls from its `write` and `flush` methods to each of the given targets.
    """

    def __init__(self, *streams: IO[str], prefix: str = '') -> None:
        self.streams = streams
        self._line_start = True
        self.prefix = prefix

    def _insert_prefix(self, data: str) -> str:
        if not self.prefix:
            return data

        # Append our prefix just after all inner newlines. Don't append to a
        # trailing newline as we don't know if the next line in the log will be
        # from this zone.
        final_newline = data.endswith('\n')
        data = data.replace('\n', '\n' + self.prefix)
        if final_newline:
            data = data[:-len(self.prefix)]
        return data

    def write(self, data: str) -> None:
        if self._line_start:
            data = self.prefix + data

        self._line_start = data.endswith('\n')
        data = self._insert_prefix(data)

        for stream in self.streams:
            stream.write(data)
        self.flush()

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


def tee_streams(name: Path, prefix: str = '') -> None:
    """
    Tee stdout and stderr also to the named log file.

    Note: we intentionally don't provide a way to clean up the stream
    replacement so that any error handling from Python which causes us to exit
    is also captured by the log file.
    """

    log_file = name.open(mode='w')

    sys.stdout = SimpleTee(  # type: ignore[assignment]
        sys.stdout,
        log_file,
        prefix=prefix,
    )
    sys.stderr = SimpleTee(  # type: ignore[assignment]
        sys.stderr,
        log_file,
        prefix=prefix,
    )
