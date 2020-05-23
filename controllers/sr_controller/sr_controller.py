import time

from sr.robot import *

R = Robot()

while True:
    print("Dist L:", R.ruggeduinos[0].analogue_read(0))
    print("Dist R:", R.ruggeduinos[0].analogue_read(1))
    R.motors[0].m0.power = 10
    R.motors[0].m1.power = 10
    R.motors[1].m1.power = 0
    time.sleep(2)
    R.motors[0].m0.power = 0
    R.motors[0].m1.power = 0
    R.motors[1].m1.power = -100
    time.sleep(2)
    R.motors[0].m0.power = -10
    R.motors[0].m1.power = -10
    R.motors[1].m1.power = 0
    time.sleep(2)
    R.motors[0].m0.power = 0
    R.motors[0].m1.power = 0
    R.motors[1].m1.power = 100
    time.sleep(2)