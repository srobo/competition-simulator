from typing import cast, Union

from sr.robot import (
    Robot,
    AnaloguePin,
    Microswitch,
    LinearEncoder,
    RotaryEncoder,
    DistanceSensor,
)
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
    "scan": (ord("R"), ord("P")),
    "boost": (Keyboard.SHIFT, Keyboard.CONTROL),
    "grabber_open": (ord("Z"), ord("N")),
    "grabber_close": (ord("X"), ord("M")),
}


def print_sensors(robot: Robot) -> None:
    distance_sensor_names = [
        "Front Left",
        "Front Right",
        "Left",
        "Right",
        "Front",
        "Back",
    ]
    touch_sensor_names = [
        "Rear",
    ]
    encoder_sensor_names = [
        "Left Wheel",
        "Right Wheel",

        "Left Gripper",
        "Right Gripper",
    ]

    pin: Union[int, AnaloguePin] = 0

    print(f"Distance sensor readings at {robot.time():.2f}s:")
    for pin, name in zip(AnaloguePin, distance_sensor_names):
        dist = cast(DistanceSensor, R.arduino.pins[pin]).analogue_value
        print(f"{pin} {name: <12}: {dist:.2f}")

    print("Touch sensor readings:")
    for pin, name in enumerate(touch_sensor_names, 2):
        touching = cast(Microswitch, R.arduino.pins[pin]).digital_state
        print(f"{pin} {name: <6}: {touching}")

    print("Encoder readings:")
    for encoder, name in enumerate(encoder_sensor_names[:2]):
        rotation = cast(RotaryEncoder, R.encoders[encoder]).rotation
        print(f"{encoder} {name: <20}: {rotation:.2f} rad")

    for encoder, name in enumerate(encoder_sensor_names[2:], 2):
        displacement = cast(LinearEncoder, R.encoders[encoder]).displacement
        print(f"{encoder} {name: <20}: {displacement:.2f}m")

    print()


R = Robot()

keyboard = Keyboard()
keyboard.enable(KEYBOARD_SAMPLING_PERIOD)

key_forward = CONTROLS["forward"][R.zone]
key_reverse = CONTROLS["reverse"][R.zone]
key_left = CONTROLS["left"][R.zone]
key_right = CONTROLS["right"][R.zone]
key_sense = CONTROLS["sense"][R.zone]
key_scan = CONTROLS["scan"][R.zone]
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

    left_power: float = 0
    right_power: float = 0
    grabber_power = 0

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

        elif key_ascii == key_scan:
            transmitters = R.radio.sweep()
            print("Found transmitter(s)")

            for transmitter in transmitters:
                print(transmitter)

            print()

        elif key_ascii == key_grab_open:
            grabber_power = 1

        elif key_ascii == key_grab_close:
            grabber_power = -1

        # Work our way through all the enqueued key presses before dropping
        # out to the timestep
        key = keyboard.getKey()

    if boost:
        # double power values but constrain to [-1, 1]
        left_power = max(min(left_power * 2, 1), -1)
        right_power = max(min(right_power * 2, 1), -1)

    R.motor_boards[0].motors[0].power = left_power
    R.motor_boards[0].motors[1].power = right_power

    R.motor_boards[1].motors[0].power = grabber_power

    R.sleep(KEYBOARD_SAMPLING_PERIOD / 1000)
