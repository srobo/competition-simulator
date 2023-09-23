from sr.robot3 import *

R = Robot()

distance = R.arduino.pins[A5].analogue_read()
print(f"Rear ultrasound distance value: {distance}")

# first motor board, channel 0 to half power forward
R.motor_board.motors[0].power = 0.5

# motor board "srABC1", channel 1 to half power forward
# using the syntax to access multiple motor boards
R.motor_boards['srABC1'].motors[1].power = 0.5

# sleep for 2 second
R.sleep(2)

# first motor board, channel 0 to stopped
R.motor_board.motors[0].power = 0

# first motor board, channel 1 to stopped
R.motor_board.motors[1].power = 0
