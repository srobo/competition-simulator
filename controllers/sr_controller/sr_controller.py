import os
import sys
import datetime
import subprocess
from shutil import copyfile
from typing import IO, Optional
from pathlib import Path

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXAMPLE_CONTROLLER_FILE = REPO_ROOT / 'controllers/example_controller/example_controller.py'

# Root directory of the specification of the Arena (and match)
ARENA_ROOT = Path(os.environ.get('ARENA_ROOT', REPO_ROOT.parent))

MODE_FILE = ARENA_ROOT / 'robot_mode.txt'
MATCH_FILE = ARENA_ROOT / 'match.txt'


ROBOT_IDS_TO_CORNERS = {
    "291": 0,
    "679": 1,
    "1067": 2,
    "1455": 3,
}

STRICT_ZONES = {
    "dev": (1, 2, 3),
    "comp": (0, 1, 2, 3),
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


def get_robot_zone() -> int:
    return ROBOT_IDS_TO_CORNERS[os.environ['WEBOTS_ROBOT_ID']]


def get_zone_robot_file_path(zone_id: int) -> Path:
    """
    Return the path to the robot.py for the given zone, without checking for
    existence.
    """
    return ARENA_ROOT / "zone-{}".format(zone_id) / "robot.py"


def get_robot_file(zone_id: int, mode: str) -> Path:
    """
    Get the path to the proper robot.py file for zone_id and mode, ensuring that
    it exists or exiting with a suitable error message.

    The logic here is that:
     - it is always an error for both a robot.py in the root and a zone-0 /
       robot.py file to exist
     - in competition mode: we check only for zone-X / robot.py files and error
       if they are missing. We assume that this controller is not run at all for
       zones which should not run.
     - in development mode:
        - zones 1-3 check only check only for zone-X / robot.py files and report
          if they are missing but exit cleanly
        - zone 0 checks for zone-0 / robot.py then a root robot.py. If neither
          are found it copies an example into place (at the root) and uses that.
    """

    robot_file = get_zone_robot_file_path(zone_id)
    fallback_robot_file = ARENA_ROOT / "robot.py"
    strict_zones = STRICT_ZONES[mode]

    if (
        robot_file.exists() and
        zone_id == 0 and
        fallback_robot_file.exists()
    ):
        exit(
            "Found robot controller in shared location and zone-0 location. "
            "Remove one of the controllers before running the simulation\n"
            "{}\n{}".format(robot_file, fallback_robot_file),
        )

    if zone_id in strict_zones:
        if robot_file.exists():
            return robot_file

        print("No robot controller found for zone {}".format(zone_id))

        # Only in competition mode is it an error for a robot file to be missing.
        missing_file_is_error = mode == "comp"
        exit(1 if missing_file_is_error else 0)

    # For the non-strict zones (i.e: Zone 0 in development mode) we check in the
    # fallback place. If that doesn't exist we copy an example into it.

    assert zone_id == 0 and mode == "dev", \
        "Unexpectedly handling fallback logic for zone {} in {} mode".format(
            zone_id,
            mode,
        )

    if robot_file.exists():
        return robot_file

    if fallback_robot_file.exists():
        return fallback_robot_file

    print("No robot controller found for zone {}, copying example to {}.".format(
        zone_id,
        fallback_robot_file,
    ))
    copyfile(str(EXAMPLE_CONTROLLER_FILE), str(fallback_robot_file))

    return fallback_robot_file


def get_robot_mode() -> str:
    if not MODE_FILE.exists():
        return "dev"
    return MODE_FILE.read_text().strip()


def print_simulation_version() -> None:
    version_path = (REPO_ROOT / '.simulation-rev')
    if version_path.exists():
        description, revision = version_path.read_text().splitlines()
        version = "{} (rev {})".format(description, revision)
    else:
        version = subprocess.check_output(
            ['git', 'describe', '--always', '--tags'],
            cwd=str(REPO_ROOT.resolve()),
        ).decode().strip()

    print("Running simulator version {}".format(version))


def reconfigure_environment(robot_file: Path) -> None:
    """
    Reconfigure the interpreter environment for the actual location of the
    competitor code.
    """

    # Remove ourselves from the path and insert the competitor code
    sys.path.pop(0)
    sys.path.insert(0, str(REPO_ROOT / "modules"))
    sys.path.insert(0, str(robot_file.parent))

    os.chdir(str(robot_file.parent))


def log_filename(zone_id: int) -> str:
    return 'log-zone-{}-{}.txt'.format(
        zone_id,
        get_filename_safe_identifier(),
    )


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

    def flush(self):
        for stream in self.streams:
            stream.flush()


def tee_streams(name: Path, zone_id: int) -> None:
    """
    Tee stdout and stderr also to the named log file.

    Note: we intentionally don't provide a way to clean up the stream
    replacement so that any error handling from Python which causes us to exit
    is also captured by the log file.
    """

    log_file = name.open(mode='w')

    prefix = '{}| '.format(zone_id)

    sys.stdout = SimpleTee(sys.stdout, log_file, prefix=prefix)  # type: ignore
    sys.stderr = SimpleTee(sys.stderr, log_file, prefix=prefix)  # type: ignore


def main():
    robot_mode = get_robot_mode()
    robot_zone = get_robot_zone()
    robot_file = get_robot_file(robot_zone, robot_mode).resolve()

    tee_streams(robot_file.parent / log_filename(robot_zone), robot_zone)

    if robot_zone == 0:
        # Only print once, but rely on Zone 0 always being run to ensure this is
        # always printed somewhere.
        print_simulation_version()

    print("Using {} for Zone {}".format(robot_file, robot_zone))

    # Pass through the various data our library needs
    os.environ['SR_ROBOT_ZONE'] = str(robot_zone)
    os.environ['SR_ROBOT_MODE'] = robot_mode
    os.environ['SR_ROBOT_FILE'] = str(robot_file)

    # Swith to running the competitor code
    reconfigure_environment(robot_file)

    exec(robot_file.read_text(), {})


if __name__ == "__main__":
    main()
