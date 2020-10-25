from sr.robot import *

R = Robot()

print("I see {} things".format(len(R.see())))

# motor board 0, channel 0 to half power forward
R.motors[0].m0.power = 50

# motor board 0, channel 1 to half power forward
R.motors[0].m1.power = 50

# sleep for 1 second
R.sleep(1)

# motor board 0, channel 0 to stopped
R.motors[0].m0.power = 0

# motor board 0, channel 1 to stopped
R.motors[0].m1.power = 0

# sleep for 2 seconds
R.sleep(2)

# motor board 0, channel 0 to half power backward
R.motors[0].m0.power = -50

# motor board 0, channel 1 to half power forward
R.motors[0].m1.power = 50

# sleep for 0.75 seconds
R.sleep(0.75)

# motor board 0, channel 0 to half power forward
R.motors[0].m0.power = 50

# motor board 0, channel 1 to half power forward
R.motors[0].m1.power = 50

# sleep for 1 second
R.sleep(1)

# motor board 0, channel 0 to stopped
R.motors[0].m0.power = 0

# motor board 0, channel 1 to stopped
R.motors[0].m1.power = 0
