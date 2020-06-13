import sys
from pathlib import Path

# Webots specific library
from controller import Supervisor  # isort:skip

sys.path.append(str(Path(__file__).resolve().parent.parent / 'sr_controller'))

sr_controller = __import__('sr_controller')

TIME_STEP = 32
GAME_DURATION_SECONDS = 10


def quit_if_development_mode() -> None:
    if sr_controller.get_robot_mode() != 'comp':
        print("Development mode, exiting competition supervisor")
        exit()


def prepare(supervisor: Supervisor) -> None:
    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)
    supervisor.simulationReset()


def remove_unused_robots(supervisor: Supervisor) -> None:
    for webots_id_str, zone_id in sr_controller.ROBOT_IDS_TO_CORNERS.items():
        if sr_controller.get_zone_robot_file_path(zone_id).exists():
            continue

        # Remove the robot
        robot = supervisor.getFromId(int(webots_id_str))
        if robot is None:
            msg = "Failed to get Webots node for zone {} (id: {})".format(
                zone_id,
                webots_id_str,
            )
            print(msg)
            raise ValueError(msg)

        robot.remove()


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
    quit_if_development_mode()

    supervisor = Supervisor()

    prepare(supervisor)

    remove_unused_robots(supervisor)

    run_match(supervisor)


if __name__ == '__main__':
    main()
