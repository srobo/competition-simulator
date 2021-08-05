from sr.robot import *

R = Robot()

print("I found {} transmitter(s):".format(len(R.radio.sweep())))

# motor board 0, channel 0 to half power forward
R.motor_boards[0].motors[0].power = 50

# motor board 0, channel 1 to half power forward
R.motor_boards[0].motors[1].power = 50

# sleep for 1 second
R.sleep(1)

# motor board 0, channel 0 to stopped
R.motor_boards[0].motors[0].power = 0

# motor board 0, channel 1 to stopped
R.motor_boards[0].motors[1].power = 0

# sleep for 2 seconds
R.sleep(2)

# motor board 0, channel 0 to half power backward
R.motor_boards[0].motors[0].power = -50

# motor board 0, channel 1 to half power forward
R.motor_boards[0].motors[1].power = 50

# sleep for 0.75 seconds
R.sleep(0.75)

# motor board 0, channel 0 to half power forward
R.motor_boards[0].motors[0].power = 50

# motor board 0, channel 1 to half power forward
R.motor_boards[0].motors[1].power = 50

# sleep for 1 second
R.sleep(1)

# motor board 0, channel 0 to stopped
R.motor_boards[0].motors[0].power = 0

# motor board 0, channel 1 to stopped
R.motor_boards[0].motors[1].power = 0
