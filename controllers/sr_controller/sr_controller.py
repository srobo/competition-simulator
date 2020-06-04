import os
import sys
import subprocess
from shutil import copyfile
from pathlib import Path

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
ROOT = Path(__file__).resolve().parent.parent.parent

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
    robot_file_dir = ROOT.parent / str(zone_id)
    if robot_file_dir.is_dir():
        return robot_file_dir / "robot.py"

    return ROOT.parent / "robot.py"


def main():
    robot_file = get_robot_file()

    if not robot_file.exists():
        print("Robot controller not found, copying example into place.")
        copyfile(str(EXAMPLE_CONTROLLER_FILE), str(robot_file))

    # Ensure the python path is properly passed down so the `sr` module can be imported
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(sys.path)

    completed_process = subprocess.run(
        [sys.executable, "-u", str(robot_file)],
        env=env,
        cwd=str(robot_file.parent),
    )

    # Exit with the same return code so webots reports it as an error
    sys.exit(completed_process.returncode)



if __name__ == "__main__":
    main()
