from sr.robot3 import *

R = Robot()

reading = R.arduino.pins[A5].analog_read()
# convert reading from volts to meters
measurement = reading / 2.5
print(f"Rear ultrasound distance {measurement:.2f} meters")

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
