from sr.robot3 import *

robot = Robot()

reading = robot.arduino.pins[A5].analog_read()
print(f"Rear ultrasound distance value: {reading}")

# first motor board, channel 0 to half power forward
robot.motor_board.motors[0].power = 0.5

# motor board "srABC1", channel 1 to half power forward
# using the syntax to access multiple motor boards
robot.motor_boards['srABC1'].motors[1].power = 0.5

# sleep for 2 second
robot.sleep(2)

# first motor board, channel 0 to stopped
robot.motor_board.motors[0].power = 0

# first motor board, channel 1 to stopped
robot.motor_board.motors[1].power = 0
