from sr.robot import Robot
from controller import Keyboard

KEYBOARD_SAMPLING_FREQUENCY = 16
NO_KEY_PRESSED = -1

CONTROLS = {
    "forward": (ord("W"), ord("I")),
    "reverse": (ord("S"), ord("K")),
    "left": (ord("A"), ord("J")),
    "right": (ord("D"), ord("L")),
    "claim": (ord("E"), ord("O")),
    "sense": (ord("Q"), ord("U")),
    "boost": (Keyboard.SHIFT, Keyboard.CONTROL),
}


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
keyboard.enable(KEYBOARD_SAMPLING_FREQUENCY)

key_forward = CONTROLS["forward"][R.zone]
key_reverse = CONTROLS["reverse"][R.zone]
key_left = CONTROLS["left"][R.zone]
key_right = CONTROLS["right"][R.zone]
key_claim = CONTROLS["claim"][R.zone]
key_sense = CONTROLS["sense"][R.zone]
key_boost = CONTROLS["boost"][R.zone]

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

            if key == key_forward:
                R.motors[0].m0.power = 50
                R.motors[0].m1.power = 50

            elif key == key_boost + key_forward:
                R.motors[0].m0.power = 100
                R.motors[0].m1.power = 100

            elif key == key_reverse:
                R.motors[0].m0.power = -50
                R.motors[0].m1.power = -50

            elif key == key_boost + key_reverse:
                R.motors[0].m0.power = -100
                R.motors[0].m1.power = -100

            elif key == key_left:
                R.motors[0].m0.power = -25
                R.motors[0].m1.power = 25

            elif key == key_right:
                R.motors[0].m0.power = 25
                R.motors[0].m1.power = -25

            elif key == key_claim:
                R.radio.claim_territory()

            elif key == key_sense:
                print_distance_sensors(R)

            # Work our way through all the enqueued key presses before dropping
            # out to the timestep
            key = keyboard.getKey()

    R.sleep(KEYBOARD_SAMPLING_FREQUENCY / 1000)
