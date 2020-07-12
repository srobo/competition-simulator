import sys
import datetime
import contextlib
from typing import Iterator
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

    return Path(date) / name / '{}.html'.format(name)


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
        caption=False)
    yield
    supervisor.movieStopRecording()


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


def prepare(supervisor: Supervisor) -> None:
    supervisor.simulationSetMode(Supervisor.SIMULATION_MODE_PAUSE)


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
    animation_recording_path = '{}.html'.format(recording_path)
    video_recording_path = '{}.mp4'.format(recording_path)

    with record_animation(supervisor, REPO_ROOT / 'recordings' / animation_recording_path):
        with record_video(supervisor, REPO_ROOT / 'recordings' / video_recording_path):
            run_match(supervisor)


if __name__ == '__main__':
    main()
