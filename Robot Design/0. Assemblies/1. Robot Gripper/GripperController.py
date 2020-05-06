"""GripperController controller."""

from controller import Robot

# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())


#
# Gripper Commands
#
GRIPPER_MAX_SPEED = 0.1
gripperMotors = []
gripperMotorNames = ['lift motor', 'left finger motor', 'right finger motor']
def moveLift (pos):
    # Make sure position is within limits
    if pos < -0.2:
        pos = -0.2
    if pos > 0.16:
        pos = 0.16
    # move to position at velocity
    gripperMotors[0].setVelocity(GRIPPER_MAX_SPEED)
    gripperMotors[0].setPosition(pos)
    
def moveFingers(pos):
    # Make sure position is within limits
    if pos < 0.0:
        pos = -0.0
    if pos > 0.15 :
        pos = 0.15
    # move to position at velocity
    gripperMotors[1].setVelocity(GRIPPER_MAX_SPEED)
    gripperMotors[2].setVelocity(GRIPPER_MAX_SPEED)
    gripperMotors[1].setPosition(pos)
    gripperMotors[2].setPosition(pos)

def initGripper():
    for i in range(len(gripperMotorNames)):
        gripperMotors.append(robot.getMotor(gripperMotorNames[i]))
    moveLift(-0.1)
    moveFingers(0)

    
# START UP:
t = 0;

# Initiate Gripper
initGripper()
#initDrive()
#drive(3.0)
# Main Loop
while robot.step(timestep) != -1:
    
    t = t + 1;
    #print(t)
    
#    drive(10)    
    
    if t == 1:
        moveLift(-0.05)
        moveFingers(0.15)
    elif t == 50:
        moveFingers(0.0)    
    elif t == 75:
        moveLift(-0.2)
    elif t == 150:
        moveFingers(0.15)
    elif t == 200:
        moveLift(-0.05)
    elif t == 225:
        t = 0
    pass

# Enter here exit cleanup code.


    
