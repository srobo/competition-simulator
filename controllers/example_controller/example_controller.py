import time

from sr.robot import *

R = Robot()

while True:
    R.motors[0].m0.power = float(50)
    R.motors[0].m1.power = float(-50)
    time.sleep(0.5)
    R.motors[0].m0.power = float(0.0)
    R.motors[0].m1.power = float(0.0)
    time.sleep(0.5)
    