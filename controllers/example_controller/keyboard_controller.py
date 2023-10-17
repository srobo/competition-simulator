import math

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
    "fingers_down": (ord("C"), ord(",")),
    "fingers_up": (ord("X"), ord(".")),
    "angle_unit": (ord("B"), ord("B")),
}

# Map robot zone to control set. Defaults to straight mapping, but provides a
# place to remap other zones if desired. Modify the keys of the dictionary to
# the zones you want to use.
ZONE_MAP = {
    0: 0,
    1: 1,
}


assert len(ZONE_MAP) == len(CONTROLS['forward']), (
    "Too many robot zones configured; inputs would control several robots at once."
)

USE_DEGREES = False


def angle_str(angle: float) -> str:
    if USE_DEGREES:
        degrees = math.degrees(angle)
        return f"{degrees:.3g}°"

    return f"{angle:.4g} rad"


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
    pressure_sensor_names = {
        A6: "Left Finger",
        A7: "Right Finger",
    }

    print(f"Distance sensor readings at {robot.time():.2f}s:")
    for Apin, name in distance_sensor_names.items():
        dist = robot.arduino.pins[Apin].analog_read()
        print(f"{Apin} {name: <12}: {dist:.2f}")

    print("Touch sensor readings:")
    for pin, name in enumerate(touch_sensor_names, 2):
        touching = robot.arduino.pins[pin].digital_read()
        print(f"{pin} {name: <6}: {touching}")

    print("Pressure sensor readings:")
    for Apin, name in pressure_sensor_names.items():
        pressure = robot.arduino.pins[Apin].analog_read()
        print(f"{Apin} {name: <12}: {pressure:.2f}")

    try:
        camera = robot.camera
    except ValueError:
        print("No camera on this robot")
    else:
        markers = camera.see()
        if markers:
            print(f"Found {len(markers)} makers:")
            for marker in markers:
                print(f" #{marker.id}")
                distance, horizontal_angle, vertical_angle = marker.position
                print(
                    f" Position: {distance}, {angle_str(horizontal_angle)}, "
                    f"{angle_str(vertical_angle)}",
                )
                yaw, pitch, roll = marker.orientation
                print(
                    f" Orientation: {angle_str(yaw)}, {angle_str(pitch)}, "
                    f"{angle_str(roll)}",
                )
                print()
        else:
            print("No markers")

    print()


robot = Robot()

if robot.zone not in ZONE_MAP:
    exit(
        f"The keyboard robot is not configured to run in zone {robot.zone}.\n"
        "Modify the `ZONE_MAP` to use the keyboard robot in other zones.",
    )


keyboard = Keyboard()
keyboard.enable(KEYBOARD_SAMPLING_PERIOD)

key_forward = CONTROLS["forward"][ZONE_MAP[robot.zone]]
key_reverse = CONTROLS["reverse"][ZONE_MAP[robot.zone]]
key_left = CONTROLS["left"][ZONE_MAP[robot.zone]]
key_right = CONTROLS["right"][ZONE_MAP[robot.zone]]
key_sense = CONTROLS["sense"][ZONE_MAP[robot.zone]]
key_boost = CONTROLS["boost"][ZONE_MAP[robot.zone]]
key_grab_open = CONTROLS["grabber_open"][ZONE_MAP[robot.zone]]
key_grab_close = CONTROLS["grabber_close"][ZONE_MAP[robot.zone]]
key_fingers_down = CONTROLS["fingers_down"][ZONE_MAP[robot.zone]]
key_fingers_up = CONTROLS["fingers_up"][ZONE_MAP[robot.zone]]
key_angle_unit = CONTROLS["angle_unit"][ZONE_MAP[robot.zone]]

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
            print_sensors(robot)

        elif key_ascii == key_grab_open:
            robot.servo_board.servos[0].position = -1
            robot.servo_board.servos[1].position = -1

        elif key_ascii == key_grab_close:
            robot.servo_board.servos[0].position = 1
            robot.servo_board.servos[1].position = 1

        elif key_ascii == key_fingers_down:
            robot.servo_board.servos[2].position = 1
            robot.servo_board.servos[3].position = 1

        elif key_ascii == key_fingers_up:
            robot.servo_board.servos[2].position = -1
            robot.servo_board.servos[3].position = -1

        elif key_ascii == key_angle_unit:
            USE_DEGREES = not USE_DEGREES

        # Work our way through all the enqueued key presses before dropping
        # out to the timestep
        key = keyboard.getKey()

    if boost:
        left_power *= 2
        right_power *= 2

    # constrain to [-1, 1] to avoid errors
    left_power = max(min(left_power, 1), -1)
    right_power = max(min(right_power, 1), -1)

    robot.motor_board.motors[0].power = left_power
    robot.motor_board.motors[1].power = right_power

    robot.sleep(KEYBOARD_SAMPLING_PERIOD / 1000)
