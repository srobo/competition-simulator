from sr.robot import Robot
from controller import Keyboard

TIMESTEP = 16
NO_KEY_PRESSED = -1


def print_distance_sensors(robot: Robot) -> None:
    distance_sensor_names = [
        "Front Left",
        "Front Right",
        "Left",
        "Right",
        "Back Left",
        "Back Right",
    ]

    print(f"Distance sensor readings at {robot.time():.2f}s:")
    for pin, name in enumerate(distance_sensor_names):
        dist = R.ruggeduinos[0].analogue_read(pin)
        print(f"{pin} {name: <12}: {dist:.2f}")

    print()


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

            elif key == ord('Q'):
                print_distance_sensors(R)

            # Work our way through all the enqueued key presses before dropping
            # out to the timestep
            key = keyboard.getKey()

    R.sleep(TIMESTEP / 1000)
