#from controller import  Motor, Camera, Robot as WebotsRobot
import time

from sr.robot import *

R = Robot()

while True:

    R.motors[0].m0.power = float(5.0)
    #R.motors[0].m1.power = float(20.0)
    R.motors[0].m1.power = float(-5.0)
    #robot.getMotor("wheel1").setVelocity(1.0)
    time.sleep(0.5)
    R.motors[0].m0.power = float(0.0)
    #R.motors[0].m1.power = float(0.0)
    R.motors[0].m1.power = float(0.0)
    time.sleep(0.5)
    