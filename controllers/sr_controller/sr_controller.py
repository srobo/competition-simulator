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
    "684": 1,
    "1077": 2,
    "1470": 3,
}


def get_robot_zone() -> int:
    return ROBOT_IDS_TO_CORNERS[os.environ['WEBOTS_ROBOT_ID']]


def get_robot_file() -> Path:
    zone_id = get_robot_zone()
    robot_file_dir = ROOT.parent / ("zone-" + str(zone_id))
    if robot_file_dir.is_dir():
        return robot_file_dir / "robot.py"
    if get_robot_mode() == "comp":
        print("WARNING: Using default robot file location in competition mode.")
    return ROOT.parent / "robot.py"


def get_robot_mode() -> str:
    if not MODE_FILE.exists():
        return "dev"
    return MODE_FILE.read_text().strip()


def main():
    robot_file = get_robot_file()
    robot_mode = get_robot_mode()
    robot_zone = get_robot_zone()

    if robot_mode == "dev" and not robot_file.exists():
        print("Robot controller not found, copying example into place.")
        copyfile(str(EXAMPLE_CONTROLLER_FILE), str(robot_file))
    elif not robot_file.exists():
        print("ERROR: No robot controller found for zone ", robot_zone)
        sys.exit(1)

    env = os.environ.copy()
    # Ensure the python path is properly passed down so the `sr` module can be imported
    env['PYTHONPATH'] = os.pathsep.join(sys.path)
    env['SR_ROBOT_ZONE'] = str(robot_zone)
    env['SR_ROBOT_MODE'] = robot_mode

    completed_process = subprocess.run(
        [sys.executable, "-u", str(robot_file)],
        env=env,
        cwd=str(robot_file.parent),
    )

    # Exit with the same return code so webots reports it as an error
    sys.exit(completed_process.returncode)


if __name__ == "__main__":
    main()
