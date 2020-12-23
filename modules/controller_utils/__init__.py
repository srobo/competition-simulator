import os
import sys
import json
import datetime
from typing import IO, Dict, List, Tuple, Optional
from pathlib import Path

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Root directory of the specification of the Arena (and match)
ARENA_ROOT = Path(os.environ.get('ARENA_ROOT', REPO_ROOT.parent))

MODE_FILE = ARENA_ROOT / 'robot_mode.txt'
MATCH_FILE = ARENA_ROOT / 'match.json'


ROBOT_IDS_TO_CORNERS = {
    "5": 0,
    "225": 1,
}
NUM_ZONES = len(ROBOT_IDS_TO_CORNERS)


def record_match_data(number: int, teams: List[Optional[str]]) -> None:
    # Use Proton format because it covers everything we need and already has a spec.
    MATCH_FILE.write_text(json.dumps({
        'match_number': number,
        'arena_id': 'Simulator',
        'teams': {
            tla: {'zone': idx}
            for idx, tla in enumerate(teams)
            if tla is not None
        },
    }, indent=4))


def record_arena_data(other_data: Dict[str, List[object]]) -> None:
    data = json.loads(MATCH_FILE.read_text())
    arena_zones = data.setdefault('arena_zones', {})
    arena_zones['other'] = other_data
    MATCH_FILE.write_text(json.dumps(data, indent=4))


def read_match_data() -> Tuple[int, List[Optional[str]]]:
    data = json.loads(MATCH_FILE.read_text())

    tla_by_zone = {x['zone']: tla for tla, x in data['teams'].items()}
    tlas = [tla_by_zone.get(i) for i in range(NUM_ZONES)]

    return data['match_number'], tlas


def get_match_num() -> Optional[int]:
    if MATCH_FILE.exists():
        match_number, _ = read_match_data()
        return match_number
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
