#from controller import  Motor, Camera, Robot as WebotsRobot
import time

from sr.robot import *



# create the Robot instance.
#robot = WebotsRobot()

# get a handler to the motors and set target position to infinity (speed control)
#leftMotor = robot.getMotor("left wheel")
#rightMotor = robot.getMotor('right wheel')
#leftMotor.setPosition(float('inf'))
#rightMotor.setPosition(float('inf'))

#robot.getMotor("M1").setPosition(float(0))
#robot.getMotor("M2").setPosition(float('inf'))
#robot.getMotor("M3").setPosition(float(0))
#robot.getMotor("M4").setPosition(float('inf'))

#robot.getMotor("M1").setVelocity(0.0)
#robot.getMotor("M2").setVelocity(0.0)
#robot.getMotor("M3").setVelocity(0.0)






R = Robot()

while True:

    R.motors[0].m0.power = float(10.0)
    #R.motors[0].m1.power = float(20.0)
    R.motors[1].m0.power = float(10.0)
    #robot.getMotor("wheel1").setVelocity(1.0)
    time.sleep(0.5)
    R.motors[0].m0.power = float(0.0)
    #R.motors[0].m1.power = float(0.0)
    R.motors[1].m0.power = float(0.0)
    time.sleep(0.5)