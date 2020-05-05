"""Arthur_BackNForth controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot
import time

TIME_STEP = 32

robot = Robot()

# Distance Sensors
ds = []
dsNames = ['DS_1', 'DS_2', 'DS_3']
for i in range(3):
    ds.append(robot.getDistanceSensor(dsNames[i]))
    ds[i].enable(TIME_STEP)
    print(ds[i].getMaxValue())
    
# Motors    
wheels = []
wheelsNames = ['M1', 'M2', 'M3', 'M4']
maxSpeed = -3.14159

for i in range(4):
    wheels.append(robot.getMotor(wheelsNames[i]))
    wheels[i].setPosition(float('inf'))
    wheels[i].setVelocity(0.0)
    
# Camera
camera = robot.getCamera('camera')
camera.enable(TIME_STEP)
camera.recognitionEnable(TIME_STEP)
obj = camera.getRecognitionObjects()
print(obj)

print("SETUP COMPLETE")

t = 0.0
tlastMove = 0.0  
foundBlock = 0
foundWall = 0

            
while robot.step(TIME_STEP) != -1:
    
    t += TIME_STEP / 1000.0

    if t < 3:
       wheels[0].setVelocity(maxSpeed)
       wheels[1].setVelocity(maxSpeed)
       wheels[2].setVelocity(maxSpeed)
       wheels[3].setVelocity(maxSpeed)
    else:
        wheels[0].setVelocity(-1* maxSpeed)
        wheels[1].setVelocity(-1 * maxSpeed)
        wheels[2].setVelocity(-1 * maxSpeed)
        wheels[3].setVelocity(-1 * maxSpeed)
    if t > 5:
        t = 0
