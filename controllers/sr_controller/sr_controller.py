import os
import sys
import subprocess
from shutil import copyfile
from pathlib import Path

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
ROOT = Path(__file__).resolve().parent.parent.parent

MODE_FILE = ROOT / "robot_mode.txt"

EXAMPLE_CONTROLLER_FILE = ROOT / "controllers/example_controller/example_controller.py"

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


def get_robot_zone() -> int:
    return ROBOT_IDS_TO_CORNERS[os.environ['WEBOTS_ROBOT_ID']]


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

    robot_file = ROOT.parent / "zone-{}".format(zone_id) / "robot.py"
    fallback_robot_file = ROOT.parent / "robot.py"
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
    version_path = (ROOT / '.simulation-rev')
    if version_path.exists():
        description, revision = version_path.read_text().splitlines()
        version = "{} (rev {})".format(description, revision)
    else:
        version = subprocess.check_output(
            ['git', 'describe', '--always', '--tags'],
            cwd=str(ROOT.resolve()),
        ).decode().strip()

    print("Running simulator version {}".format(version))


def reconfigure_environment(robot_file: Path) -> None:
    """
    Reconfigure the interpreter environment for the actual location of the
    competitor code.
    """

    # Remove ourselves from the path and insert the competitor code
    sys.path.pop()
    sys.path.insert(0, str(ROOT / "modules"))
    sys.path.insert(0, str(robot_file.parent))

    os.chdir(str(robot_file.parent))


def main():
    robot_mode = get_robot_mode()
    robot_zone = get_robot_zone()
    robot_file = get_robot_file(robot_zone, robot_mode).resolve()

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
