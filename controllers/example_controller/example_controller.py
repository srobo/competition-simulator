from controller import  Motor, Camera, Robot as WebotsRobot
import time
from threading import Thread
from sr.robot import *

TIME_STEP = 64

MAX_SPEED = 12.3

# create the Robot instance.
robot = WebotsRobot()

# get a handler to the motors and set target position to infinity (speed control)
#leftMotor = robot.getMotor("left wheel")
#rightMotor = robot.getMotor('right wheel')
#leftMotor.setPosition(float('inf'))
#rightMotor.setPosition(float('inf'))

robot.getMotor("wheel1").setPosition(float('inf'))
robot.getMotor("wheel2").setPosition(float('inf'))
#robot.getMotor("M3").setPosition(float('inf'))
#robot.getMotor("M4").setPosition(float('inf'))

robot.getMotor("wheel1").setVelocity(0.0)
robot.getMotor("wheel2").setVelocity(0.0)

def run_robot():
  while not robot.step(TIME_STEP):
    pass
t = Thread(target=run_robot)
t.start()

time.sleep(TIME_STEP / 1000)

R = Robot(robot)

while True:

    R.motors[0].m0.power = float(1.0)
    R.motors[0].m1.power = float(0.0)
    #robot.getMotor("wheel1").setVelocity(1.0)
    time.sleep(0.5)
    R.motors[0].m0.power = float(0.0)
    R.motors[0].m1.power = float(1.0)
    time.sleep(0.5)