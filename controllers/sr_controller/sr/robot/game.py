import time
import _thread
from threading import Timer
from sr.robot.settings import GAME_DURATION
from textwrap import dedent

def game_over():
    print(dedent("""
    ==========
    Game Over!
    ==========
    """).strip())
    _thread.interrupt_main()


def stop_after_delay(delay=GAME_DURATION):
    Timer(delay, game_over).start()
