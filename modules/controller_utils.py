import os
import datetime
from typing import IO, Optional
from pathlib import Path

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent

# Root directory of the specification of the Arena (and match)
ARENA_ROOT = Path(os.environ.get('ARENA_ROOT', REPO_ROOT.parent))

MODE_FILE = ARENA_ROOT / 'robot_mode.txt'
MATCH_FILE = ARENA_ROOT / 'match.txt'


ROBOT_IDS_TO_CORNERS = {
    "5": 0,
    "225": 1,
}


def get_match_num() -> Optional[int]:
    if MATCH_FILE.exists():
        return int(MATCH_FILE.read_text().strip())
    return None


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


def get_zone_robot_file_path(zone_id: int) -> Path:
    """
    Return the path to the robot.py for the given zone, without checking for
    existence.
    """
    return ARENA_ROOT / "zone-{}".format(zone_id) / "robot.py"


def get_robot_mode() -> str:
    if not MODE_FILE.exists():
        return "dev"
    return MODE_FILE.read_text().strip()


class SimpleTee:
    """
    Forwards calls from its `write` and `flush` methods to each of the given targets.
    """

    def __init__(self, *streams: IO[str], prefix: str = '') -> None:
        self.streams = streams
        self._line_start = True
        self.prefix = prefix

    def _insert_prefix(self, data: str) -> str:
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