import sys
import time
import contextlib
from typing import List, Tuple, Iterator, TYPE_CHECKING
from pathlib import Path

import pkg_resources
# Webots specific library
from controller import Node, Supervisor

if TYPE_CHECKING:
    from controller import SimulationMode

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(1, str(REPO_ROOT / 'modules'))

import controller_utils  # isort:skip


@contextlib.contextmanager
def record_animation(supervisor: Supervisor, file_path: Path) -> Iterator[None]:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    print("Saving animation to {}".format(file_path))
    supervisor.animationStartRecording(str(file_path))
    yield
    supervisor.animationStopRecording()


@contextlib.contextmanager
def record_video(supervisor: Supervisor, file_path: Path) -> Iterator[None]:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    print("Saving video to {}".format(file_path))

    config = controller_utils.get_recording_config()
    supervisor.movieStartRecording(
        str(file_path),
        width=config.resolution.width,
        height=config.resolution.height,
        quality=config.quality,
        codec=0,
        acceleration=1,
        caption=False,
    )
    yield
    supervisor.movieStopRecording()

    while not supervisor.movieIsReady():
        time.sleep(0.1)

    if supervisor.movieFailed():
        print("Movie failed to record")


@contextlib.contextmanager
def propagate_exit_code(supervisor: Supervisor) -> Iterator[None]:
    try:
        yield
    except Exception:
        supervisor.simulationQuit(1)
        raise
    else:
        supervisor.simulationQuit(0)


def quit_if_development_mode() -> None:
    if controller_utils.get_robot_mode() != 'comp':
        print("Development mode, exiting competition supervisor")
        exit()


def check_required_libraries(path: Path) -> None:
    missing, incorrect = [], []

    for package in path.read_text().splitlines():
        package = package.partition('#')[0].strip()
        if not package:
            continue

        try:
            pkg_resources.get_distribution(package)
        except pkg_resources.DistributionNotFound:
            missing.append(package)
        except pkg_resources.VersionConflict:
            incorrect.append(package)

    if missing or incorrect:
        raise RuntimeError(
            "Required packages are missing ({!r}) or incorrect ({!r}). Have you "
            "installed {}?".format(missing, incorrect, path.relative_to(REPO_ROOT)),
        )


def get_robots(supervisor: Supervisor) -> List[Tuple[int, Node]]:
    robots = []  # List[Tuple[int, Supervisor]]

    for webots_id_str, zone_id in controller_utils.ROBOT_IDS_TO_CORNERS.items():
        robot = supervisor.getFromId(int(webots_id_str))
        if robot is None:
            msg = "Failed to get Webots node for zone {} (id: {})".format(
                zone_id,
                webots_id_str,
            )
            print(msg)
            raise ValueError(msg)

        robots.append((zone_id, robot))

    return robots


def wait_until_robots_ready(supervisor: Supervisor) -> None:
    time_step = int(supervisor.getBasicTimeStep())

    for zone_id, robot in get_robots(supervisor):
        # Robot.wait_start sets this to 'ready', then waits to see 'start'
        field = robot.getField('customData')

        if field.getSFString() != 'ready':
            print("Waiting for {}".format(zone_id))
            while field.getSFString():
                supervisor.step(time_step)

        print("Zone {} ready".format(zone_id))


def prepare(supervisor: Supervisor) -> None:
    wait_until_robots_ready(supervisor)
    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)


def remove_unused_robots(supervisor: Supervisor) -> None:
    for zone_id, robot in get_robots(supervisor):
        if controller_utils.get_zone_robot_file_path(zone_id).exists():
            continue

        robot.remove()


def get_simulation_run_mode(supervisor: Supervisor) -> 'SimulationMode':
    # webots 2020b is buggy and can raise TypeError when getDevice is passed a str
    if supervisor.getDevice("2021a-compatibility") is None:
        # we are running version 2020b so the old command is used
        return Supervisor.SIMULATION_MODE_RUN
    else:
        # webots-2021a removed the RUN mode and now uses FAST
        print(
            "This simulator is running a different version of Webots to the "
            "one that will be used for the next official competition matches "
            "(You can check the docs to see which version will be used)",
            file=sys.stderr,
        )
        print(
            "As such it is possible that some behaviour may not "
            "match that of the official competition matches",
            file=sys.stderr,
        )
        return Supervisor.SIMULATION_MODE_FAST


def run_match(supervisor: Supervisor) -> None:
    print("===========")
    print("Match start")
    print("===========")

    # First signal the robot controllers that they're able to start ...
    for _, robot in get_robots(supervisor):
        robot.getField('customData').setSFString('start')

    # ... then un-pause the simulation, so they all start together
    supervisor.simulationSetMode(get_simulation_run_mode(supervisor))

    time_step = int(supervisor.getBasicTimeStep())
    duration = controller_utils.get_match_duration_seconds()
    duration_ms = time_step * int(1000 * duration // time_step)
    supervisor.step(duration_ms)

    print("==================")
    print("Game over, pausing")
    print("==================")

    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)


def main() -> None:
    quit_if_development_mode()

    controller_utils.tee_streams(
        controller_utils.get_competition_supervisor_log_filepath(),
    )

    supervisor = Supervisor()

    with propagate_exit_code(supervisor):
        prepare(supervisor)

        # Check after we've paused the sim so that any errors won't be masked by
        # subsequent console output from a robot.
        check_required_libraries(REPO_ROOT / 'libraries.txt')

        remove_unused_robots(supervisor)

        recording_stem = controller_utils.get_recording_stem()

        with record_animation(supervisor, recording_stem.with_suffix('.html')):
            with record_video(supervisor, recording_stem.with_suffix('.mp4')):
                run_match(supervisor)


if __name__ == '__main__':
    main()
