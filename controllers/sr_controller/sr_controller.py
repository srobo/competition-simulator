import os
import sys
from shutil import copyfile
from pathlib import Path

ROOT = Path(os.getcwd()).joinpath("../../").resolve()

CONTROLLER_NAME = "robot"
CONTROLLER_FILENAME = CONTROLLER_NAME + ".py"

ROBOT_FILE_DIR = ROOT.parent

ROBOT_FILE = ROBOT_FILE_DIR.joinpath(CONTROLLER_FILENAME)

EXAMPLE_CONTROLLER_FILE =ROOT.joinpath("controllers/example_controller/example_controller.py").resolve()


if __name__ == "__main__":
    if not ROBOT_FILE.exists():
        print("Robot controller not found, copying example into place.")
        copyfile(EXAMPLE_CONTROLLER_FILE, ROBOT_FILE)

    sys.path.insert(0, str(ROBOT_FILE_DIR))
    __import__(CONTROLLER_NAME)
