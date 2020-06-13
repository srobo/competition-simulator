import time
from pathlib import Path

# Webots specific library
from controller import Supervisor  # isort:skip

GAME_DURATION_SECONDS = 10

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
ROOT = Path(__file__).resolve().parent.parent.parent

MODE_FILE = ROOT / 'robot_mode.txt'

if not MODE_FILE.exists() or MODE_FILE.read_text().strip() != 'comp':
    print("Development mode, exiting competition supervisor")
    exit()

supervisor = Supervisor()

supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)
supervisor.simulationReset()

# TODO: connect up to wait_start and remove robots which are not present.

supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_REAL_TIME)

end = time.time() + GAME_DURATION_SECONDS

while time.time() < end:
    supervisor.step(32)

print("==================")
print("Game over, pausing")
print("==================")

supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)
