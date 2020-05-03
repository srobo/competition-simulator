from controller import  Motor, Camera, Robot as WebotsRobot
import time
from threading import Thread

TIME_STEP = 64

MAX_SPEED = 12.3

# create the Robot instance.
robot = WebotsRobot()

# get a handler to the motors and set target position to infinity (speed control)
leftMotor = robot.getMotor("left wheel")
rightMotor = robot.getMotor('right wheel')
leftMotor.setPosition(float('inf'))
rightMotor.setPosition(float('inf'))

def run_robot():
  while not robot.step(TIME_STEP):
    pass
t = Thread(target=run_robot)
t.start()

time.sleep(TIME_STEP / 1000)

# print(dir(robot))

# set up the motor speeds at 10% of the MAX_SPEED.
while True:
  leftMotor.setVelocity(MAX_SPEED)
  rightMotor.setVelocity(MAX_SPEED)
  
  time.sleep(1)
  
  leftMotor.setVelocity(0)
  rightMotor.setVelocity(0)
  
  time.sleep(0.25)
  
  leftMotor.setVelocity(-MAX_SPEED / 2)
  rightMotor.setVelocity(MAX_SPEED / 2)
  
  time.sleep(0.5)
  
  leftMotor.setVelocity(0)
  rightMotor.setVelocity(0)
  
  time.sleep(0.25)


  