from sr.robot import *
import time

R = Robot()

print("I see {} things".format(len(R.see())))

# motor board 0, channel 0 to half power forward
R.motors[0].m0.power = 50

# motor board 0, channel 1 to half power forward
R.motors[0].m1.power = 50

# sleep for 1 second
time.sleep(1)

# motor board 0, channel 0 to stopped
R.motors[0].m0.power = 0

# motor board 0, channel 1 to stopped
R.motors[0].m1.power = 0

# sleep for 2 seconds
time.sleep(2)

# motor board 0, channel 0 to half power backward
R.motors[0].m0.power = -50

# motor board 0, channel 1 to half power forward
R.motors[0].m1.power = 50

# sleep for 0.75 seconds
time.sleep(0.75)

# motor board 0, channel 0 to half power forward
R.motors[0].m0.power = 50

# motor board 0, channel 1 to half power forward
R.motors[0].m1.power = 50

# sleep for 1 second
time.sleep(1)

# motor board 0, channel 0 to stopped
R.motors[0].m0.power = 0

# motor board 0, channel 1 to stopped
R.motors[0].m1.power = 0
