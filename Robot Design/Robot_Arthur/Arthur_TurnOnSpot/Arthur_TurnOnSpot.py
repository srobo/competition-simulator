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
    wheels[0].setVelocity(0.5 * maxSpeed)
    wheels[1].setVelocity(0.5 * maxSpeed)
    wheels[2].setVelocity(-0.5 * maxSpeed)
    wheels[3].setVelocity(-0.5 * maxSpeed)
    