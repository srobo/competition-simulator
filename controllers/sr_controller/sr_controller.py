import os
import sys
import subprocess
from shutil import copyfile
from pathlib import Path

ROOT = Path().joinpath("../../").resolve()

ROBOT_FILE = ROOT.parent.joinpath("robot.py")

EXAMPLE_CONTROLLER_FILE = ROOT.joinpath("controllers/example_controller/example_controller.py")


if __name__ == "__main__":
    if not ROBOT_FILE.exists():
        print("Robot controller not found, copying example into place.")
        copyfile(str(EXAMPLE_CONTROLLER_FILE), str(ROBOT_FILE))

    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(sys.path)

    completed_process = subprocess.run([sys.executable, "-u", str(ROBOT_FILE)], env=env)
    sys.exit(completed_process.returncode)
