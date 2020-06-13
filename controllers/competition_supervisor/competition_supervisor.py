from pathlib import Path

# Webots specific library
from controller import Supervisor  # isort:skip

TIME_STEP = 32
GAME_DURATION_SECONDS = 10

# Root directory of the SR webots simulator (equivalent to the root of the git repo)
ROOT = Path(__file__).resolve().parent.parent.parent

MODE_FILE = ROOT / 'robot_mode.txt'

if not MODE_FILE.exists() or MODE_FILE.read_text().strip() != 'comp':
    print("Development mode, exiting competition supervisor")
    exit()


def prepare(supervisor: Supervisor) -> None:
    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)
    supervisor.simulationReset()


def run_match(supervisor: Supervisor) -> None:
    print("===========")
    print("Match start")
    print("===========")

    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_REAL_TIME)

    duration_ms = TIME_STEP * int(1000 * GAME_DURATION_SECONDS // TIME_STEP)
    supervisor.step(duration_ms)

    print("==================")
    print("Game over, pausing")
    print("==================")

    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)


def main() -> None:
    supervisor = Supervisor()

    prepare(supervisor)

    # TODO: connect up to wait_start and remove robots which are not present.

    run_match(supervisor)


if __name__ == '__main__':
    main()
