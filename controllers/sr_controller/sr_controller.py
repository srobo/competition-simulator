import os
import sys
import subprocess
from shutil import copyfile
from pathlib import Path

ROOT = Path().joinpath("../../").resolve()

ROBOT_FILE_DIR = ROOT.parent
ROBOT_FILE = ROOT.parent.joinpath("robot.py")

EXAMPLE_CONTROLLER_FILE = ROOT.joinpath("controllers/example_controller/example_controller.py")


if __name__ == "__main__":
    if not ROBOT_FILE.exists():
        print("Robot controller not found, copying example into place.")
        copyfile(str(EXAMPLE_CONTROLLER_FILE), str(ROBOT_FILE))

    # Ensure the python path is properly passed down so the `sr` module can be imported
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(sys.path + [str(ROBOT_FILE_DIR)])

    completed_process = subprocess.run([sys.executable, "-u", str(ROBOT_FILE)], env=env, cwd=str(ROBOT_FILE_DIR))

    # Exit with the same return code so webots reports it as an error
    sys.exit(completed_process.returncode)
