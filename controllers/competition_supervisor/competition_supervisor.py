import sys
import time
import datetime
import contextlib
from typing import List, Tuple, Iterator
from pathlib import Path

import pkg_resources

# Webots specific library
from controller import Supervisor  # isort:skip

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.append(str(REPO_ROOT / 'controllers/sr_controller'))

import sr_controller  # noqa:E402 # isort:skip

GAME_DURATION_SECONDS = 150


def get_recording_path() -> Path:
    now = datetime.datetime.now()

    date = now.date().isoformat()

    name = sr_controller.get_filename_safe_identifier()  # type: str

    return Path(date) / name


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
    supervisor.movieStartRecording(
        str(file_path),
        width=1920,
        height=1080,
        quality=100,
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


def quit_if_development_mode() -> None:
    if sr_controller.get_robot_mode() != 'comp':
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


def get_robots(supervisor: Supervisor) -> List[Tuple[int, Supervisor]]:
    robots = []  # List[Tuple[int, Supervisor]]

    for webots_id_str, zone_id in sr_controller.ROBOT_IDS_TO_CORNERS.items():
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


def prepare(supervisor: Supervisor) -> None:
    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)
    supervisor.simulationReset()

    for _, robot in get_robots(supervisor):
        robot.restartController()

    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_REAL_TIME)


def remove_unused_robots(supervisor: Supervisor) -> None:
    for zone_id, robot in get_robots(supervisor):
        if sr_controller.get_zone_robot_file_path(zone_id).exists():
            continue

        robot.remove()


def run_match(supervisor: Supervisor) -> None:
    print("===========")
    print("Match start")
    print("===========")

    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_REAL_TIME)

    time_step = int(supervisor.getBasicTimeStep())
    duration_ms = time_step * int(1000 * GAME_DURATION_SECONDS // time_step)
    supervisor.step(duration_ms)

    print("==================")
    print("Game over, pausing")
    print("==================")

    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)


def main() -> None:
    quit_if_development_mode()

    supervisor = Supervisor()

    prepare(supervisor)

    # Check after we've paused the sim so that any errors won't be masked by
    # subsequent console output from a robot.
    check_required_libraries(REPO_ROOT / 'libraries.txt')

    remove_unused_robots(supervisor)

    recording_path = get_recording_path()
    animation_recording_path = recording_path.with_suffix('.html')
    video_recording_path = recording_path.with_suffix('.mp4')

    with record_animation(supervisor, REPO_ROOT / 'recordings' / animation_recording_path):
        with record_video(supervisor, REPO_ROOT / 'recordings' / video_recording_path):
            run_match(supervisor)

    # Give the user time to notive any error messages
    time.sleep(5)

    # Quit, the next round will get a fresh instance
    supervisor.simulationQuit(0)


if __name__ == '__main__':
    main()
