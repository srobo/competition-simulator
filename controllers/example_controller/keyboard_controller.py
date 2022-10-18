from sr.robot3 import *
from controller import Keyboard

# Any keys still pressed in the following period will be handled again
# leading to repeated claim attempts or printing sensors multiple times
KEYBOARD_SAMPLING_PERIOD = 100
NO_KEY_PRESSED = -1

CONTROLS = {
    "forward": (ord("W"), ord("I")),
    "reverse": (ord("S"), ord("K")),
    "left": (ord("A"), ord("J")),
    "right": (ord("D"), ord("L")),
    "sense": (ord("Q"), ord("U")),
    "boost": (Keyboard.SHIFT, Keyboard.CONTROL),
    "grabber_open": (ord("R"), ord("P")),
    "grabber_close": (ord("E"), ord("O")),
}


def print_sensors(robot: Robot) -> None:
    distance_sensor_names = {
        A0: "Front Left",
        A1: "Front Right",
        A2: "Left",
        A3: "Right",
        A4: "Front",
        A5: "Back",
    }
    touch_sensor_names = [
        "Rear",
    ]

    print(f"Distance sensor readings at {robot.time():.2f}s:")
    for Apin, name in distance_sensor_names.items():
        dist = R.ruggeduino.pins[Apin].analogue_read()
        print(f"{Apin} {name: <12}: {dist:.2f}")

    print("Touch sensor readings:")
    for pin, name in enumerate(touch_sensor_names, 2):
        touching = R.ruggeduino.pins[pin].digital_read()
        print(f"{pin} {name: <6}: {touching}")

    try:
        camera = R.camera
    except ValueError:
        print("No camera on this robot")
    else:
        markers = camera.see()
        if markers:
            print(f"Found {len(markers)} makers:")
            for marker in markers:
                print(f" #{marker.id}")
                x, y, z = marker.cartesian
                print(f" Cartesian: {x:.4g}, {y:.4g}, {z:.4g}")
                rot_x, rot_y, dist = marker.spherical
                print(f" Spherical: {rot_x:.4g}, {rot_y:.4g}, {dist}")
                rot_x, rot_y, rot_z = marker.orientation
                print(f" Orientation: {rot_x:.4g}, {rot_y:.4g}, {rot_z:.4g}")
                print()
        else:
            print("No markers")

    print()


R = Robot()

keyboard = Keyboard()
keyboard.enable(KEYBOARD_SAMPLING_PERIOD)

key_forward = CONTROLS["forward"][R.zone]
key_reverse = CONTROLS["reverse"][R.zone]
key_left = CONTROLS["left"][R.zone]
key_right = CONTROLS["right"][R.zone]
key_sense = CONTROLS["sense"][R.zone]
key_boost = CONTROLS["boost"][R.zone]
key_grab_open = CONTROLS["grabber_open"][R.zone]
key_grab_close = CONTROLS["grabber_close"][R.zone]

print(
    "Note: you need to click on 3D viewport for keyboard events to be picked "
    "up by webots",
)

while True:
    key = keyboard.getKey()

    boost = False

    left_power = 0.0
    right_power = 0.0

    while key != NO_KEY_PRESSED:
        key_ascii = key & 0x7F  # mask out modifier keys
        # note: modifiers are only recorded when pressed before other keys
        key_mod = key & (~0x7F)

        if key_mod == key_boost:
            boost = True

        if key_ascii == key_forward:
            left_power += 0.5
            right_power += 0.5

        elif key_ascii == key_reverse:
            left_power += -0.5
            right_power += -0.5

        elif key_ascii == key_left:
            left_power -= 0.25
            right_power += 0.25

        elif key_ascii == key_right:
            left_power += 0.25
            right_power -= 0.25

        elif key_ascii == key_sense:
            print_sensors(R)

        elif key_ascii == key_grab_open:
            R.servo_board.servos[0].position = -1
            R.servo_board.servos[1].position = -1

        elif key_ascii == key_grab_close:
            R.servo_board.servos[0].position = 1
            R.servo_board.servos[1].position = 1

        # Work our way through all the enqueued key presses before dropping
        # out to the timestep
        key = keyboard.getKey()

    if boost:
        # double power values but constrain to [-1, 1]
        left_power = max(min(left_power * 2, 1), -1)
        right_power = max(min(right_power * 2, 1), -1)

    R.motor_board.motors[0].power = left_power
    R.motor_board.motors[1].power = right_power

    R.sleep(KEYBOARD_SAMPLING_PERIOD / 1000)
