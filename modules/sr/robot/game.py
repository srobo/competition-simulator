from textwrap import dedent
from threading import Timer

import _thread
from sr.robot.settings import GAME_DURATION


def game_over():
    print(dedent("""
    ==========
    Game Over!
    ==========
    """).strip())  # noqa:T001
    _thread.interrupt_main()


def stop_after_delay(delay=GAME_DURATION):
    Timer(delay, game_over).start()
