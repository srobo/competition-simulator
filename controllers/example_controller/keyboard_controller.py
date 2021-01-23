from sr.robot import Robot
from controller import Keyboard

TIMESTEP = 16
NO_KEY_PRESSED = -1

R = Robot()

keyboard = Keyboard()
keyboard.enable(TIMESTEP)

print(
    "Note: you need to click on 3D viewport for keyboard events to be picked "
    "up by webots",
)

while True:
    key = keyboard.getKey()
    if key == NO_KEY_PRESSED:
        R.motors[0].m0.power = 0
        R.motors[0].m1.power = 0
    else:
        while key != NO_KEY_PRESSED:
            if key == ord('W'):
                R.motors[0].m0.power = 50
                R.motors[0].m1.power = 50
            elif key == ord('S'):
                R.motors[0].m0.power = -50
                R.motors[0].m1.power = -50
            elif key == ord('A'):
                R.motors[0].m0.power = -25
                R.motors[0].m1.power = 25
            elif key == ord('D'):
                R.motors[0].m0.power = 25
                R.motors[0].m1.power = -25
            elif key == ord('E'):
                R.radio.claim_territory()

            # Work our way through all the enqueued key presses before dropping
            # out to the timestep
            key = keyboard.getKey()

    R.sleep(TIMESTEP / 1000)
