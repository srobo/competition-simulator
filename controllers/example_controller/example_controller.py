import time

from sr.robot import *

R = Robot()

while True:
    R.motors[0].m0.power = 90
    R.motors[0].m1.power = 90
    time.sleep(5)
    R.motors[0].m0.power = 70
    R.motors[0].m1.power = -70
    time.sleep(0.8)
    R.motors[0].m0.power = -80
    R.motors[0].m1.power = -80
    time.sleep(0.3)
    R.motors[0].m0.power = 0
    R.motors[0].m1.power = 0
    time.sleep(0.5)
    