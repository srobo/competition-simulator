import time
import _thread
from threading import Timer
from sr.robot.settings import GAME_DURATION


def stop_after_delay(delay=GAME_DURATION):
    def game_over():
        print("Game over!")
        _thread.interrupt_main()

    Timer(delay, game_over).start()
