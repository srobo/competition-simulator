from sr.robot import *

R = Robot()

distance = R.ruggeduino.pins[A5].analogue_read()
print(f"Rear ultrasound distance: {distance} meters")

# first motor board, channel 0 to half power forward
R.motor_board.motors[0].power = 0.5

# motor board "srABC1", channel 1 to half power forward
# using the syntax to access multiple motor boards
R.motor_boards['srABC1'].motors[1].power = 0.5

# sleep for 1 second
R.sleep(1)

# first motor board, channel 0 to stopped
R.motor_board.motors[0].power = 0

# first motor board, channel 1 to stopped
R.motor_board.motors[1].power = 0

# sleep for 2 seconds
R.sleep(2)

# Turn on the green LED, connected to pin 4
R.ruggeduino.pins[4].digital_write(True)

# first motor board, channel 0 to half power backward
R.motor_board.motors[0].power = -0.5

# first motor board, channel 1 to half power forward
R.motor_board.motors[1].power = 0.5

# sleep for 0.75 seconds
R.sleep(0.25)

# first motor board, channel 0 to half power forward
R.motor_board.motors[0].power = 0.5

# first motor board, channel 1 to half power forward
R.motor_board.motors[1].power = 0.5

# sleep for 1 second
R.sleep(1)

# first motor board, channel 0 to stopped
R.motor_board.motors[0].power = 0

# first motor board, channel 1 to stopped
R.motor_board.motors[1].power = 0
