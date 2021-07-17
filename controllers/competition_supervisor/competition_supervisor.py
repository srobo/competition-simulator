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

from shared_utils import RobotType  # isort:skip
import controller_utils  # isort:skip
import webots_utils  # isort:skip


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

    config = controller_utils.get_recording_config()
    if config.quality == 0:
        print('Not recording movie')
        yield
        return
    else:
        print("Saving video to {}".format(file_path))

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
    """
    Quit the simulation at the end of a block, with an exit code indicating
    whether or not an error happened.

    This ensures that any errors in the supervisor are propagated outwards to
    the caller, which is useful during automated running of matches.
    """
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
            f"Required packages are missing ({missing!r}) or incorrect ({incorrect!r}). "
            f"Have you installed {path.relative_to(REPO_ROOT)}?\n"
            f"Hint: maybe you need to run 'pip install -r {path.relative_to(REPO_ROOT)}'?",
        )


def get_robots(
    supervisor: Supervisor,
    *,
    skip_missing: bool = False
) -> List[Tuple[int, RobotType, Node]]:
    """
    Get a list of (zone id, robot node) tuples.

    By default this raises a `ValueError` if it fails to fetch a robot node for
    a given zone, however this behaviour can be altered if the caller wishes to
    instead skip the missing nodes. This should only be done if the caller has
    already validated that the node ids being used for the lookups are
    definitely valid (and that therefore missing nodes are expected rather than
    a signal of an internal error).
    """

    robots = []  # List[Tuple[int, Supervisor]]

    for zone_id in range(controller_utils.NUM_ZONES):
        for robot_type in RobotType:
            robot = supervisor.getFromDef(f"ROBOT-{zone_id}-{robot_type.value}")
            if robot is None:
                if skip_missing:
                    continue

                msg = "Failed to get Webots node for zone {} and type {}".format(
                    zone_id,
                    robot_type.value,
                )
                print(msg)
                raise ValueError(msg)

            robots.append((zone_id, robot_type, robot))

    return robots


def wait_until_robots_ready(supervisor: Supervisor) -> None:
    time_step = int(supervisor.getBasicTimeStep())

    for zone_id, robot_type, robot in get_robots(supervisor, skip_missing=True):
        # Robot.wait_start sets this to 'ready', then waits to see 'start'
        field = robot.getField('customData')

        if field.getSFString() != 'ready':
            print("Waiting for {}".format(zone_id))
            end_time = supervisor.getTime() + 5
            while field.getSFString() != 'ready':
                # 5 second initialisation timeout
                if supervisor.getTime() > end_time:
                    raise RuntimeError(
                        f"Robot in zone {zone_id} failed to initialise. "
                        "Check whether the robot code is correctly reaching and "
                        "calling `wait_start`.",
                    )
                supervisor.step(time_step)

        print("Zone {} ready".format(zone_id))


def remove_unused_robots(supervisor: Supervisor) -> None:
    for zone_id, robot_type, robot in get_robots(supervisor):
        if controller_utils.get_zone_robot_file_path(zone_id, robot_type).exists():
            continue

        robot.remove()


def get_simulation_run_mode(supervisor: Supervisor) -> 'SimulationMode':
    # webots 2020b is buggy and can raise TypeError when getDevice is passed a str
    if supervisor.getDevice("2021a-compatibility") is None:
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
        # we are running version 2020b so the old command is used
        return Supervisor.SIMULATION_MODE_RUN
    else:
        # webots-2021a removed the RUN mode and now uses FAST
        return Supervisor.SIMULATION_MODE_FAST


def inform_start(node: Node) -> None:
    node.getField('customData').setSFString('start')


def run_match(supervisor: Supervisor) -> None:
    print("===========")
    print("Match start")
    print("===========")

    # First signal the robot controllers that they're able to start ...
    for _, _, robot in get_robots(supervisor, skip_missing=True):
        inform_start(robot)
    inform_start(webots_utils.node_from_def(supervisor, 'WALL_CTRL'))
    inform_start(webots_utils.node_from_def(supervisor, 'LIGHT_CTRL'))

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
        remove_unused_robots(supervisor)
        wait_until_robots_ready(supervisor)

        supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)

        # Check after we've paused the sim so that any errors won't be masked by
        # subsequent console output from a robot.
        check_required_libraries(REPO_ROOT / 'libraries.txt')

        recording_stem = controller_utils.get_recording_stem()

        with record_animation(supervisor, recording_stem.with_suffix('.html')):
            with record_video(supervisor, recording_stem.with_suffix('.mp4')):
                run_match(supervisor)


if __name__ == '__main__':
    main()
