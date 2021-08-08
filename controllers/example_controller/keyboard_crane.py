from typing import cast

from sr.robot import Robot, AnaloguePin, LinearEncoder, DistanceSensor
from controller import Keyboard

# Any keys still pressed in the following period will be handled again
# leading to repeated claim attempts or printing sensors multiple times
KEYBOARD_SAMPLING_PERIOD = 100
NO_KEY_PRESSED = -1

CONTROLS = {
    "north": (ord("W"), ord("I")),
    "south": (ord("S"), ord("K")),
    "left": (ord("A"), ord("J")),
    "right": (ord("D"), ord("L")),
    "up": (ord("Z"), ord("N")),
    "down": (ord("X"), ord("M")),

    "sense": (ord("Q"), ord("U")),
    "grab": (ord("E"), ord("O")),
    "boost": (Keyboard.SHIFT, Keyboard.CONTROL),
}


def print_sensors(robot: Robot) -> None:
    encoder_sensor_names = [
        "Bridge (north-south)",
        "Trolley (left-right)",
        "Hoist (up-down)",
    ]
    distance_sensor_names = ["Hook DS"]

    transmitters = R.radio.sweep()
    print("Found transmitter(s):")

    for transmitter in transmitters:
        print(transmitter)

    print("Encoder readings:")
    for encoder, name in enumerate(encoder_sensor_names):
        displacement = cast(LinearEncoder, R.encoders[encoder]).displacement
        print(f"{encoder} {name: <20}: {displacement:.2f}m")

    print(f"Distance sensor readings at {robot.time():.2f}s:")
    for pin, name in zip(AnaloguePin, distance_sensor_names):
        dist = cast(DistanceSensor, R.arduino.pins[pin]).analogue_value
        print(f"{pin} {name: <12}: {dist:.2f}")


R = Robot()

keyboard = Keyboard()
keyboard.enable(KEYBOARD_SAMPLING_PERIOD)

key_north = CONTROLS["north"][R.zone]
key_south = CONTROLS["south"][R.zone]
key_left = CONTROLS["left"][R.zone]
key_right = CONTROLS["right"][R.zone]
key_up = CONTROLS["up"][R.zone]
key_down = CONTROLS["down"][R.zone]

key_grab = CONTROLS["grab"][R.zone]
key_sense = CONTROLS["sense"][R.zone]
key_boost = CONTROLS["boost"][R.zone]

print(
    "Note: you need to click on 3D viewport for keyboard events to be picked "
    "up by webots",
)

while True:
    key = keyboard.getKey()

    boost = False

    bridge_power = 0.0
    trolley_power = 0.0
    hoist_power = 0.0

    while key != NO_KEY_PRESSED:
        key_ascii = key & 0x7F  # mask out modifier keys
        # note: modifiers are only recorded when pressed before other keys
        key_mod = key & (~0x7F)

        if key_mod == key_boost:
            boost = True

        if key_ascii == key_north:
            bridge_power = 0.5

        elif key_ascii == key_south:
            bridge_power = -0.5

        elif key_ascii == key_left:
            trolley_power = -0.5

        elif key_ascii == key_right:
            trolley_power = 0.5

        elif key_ascii == key_up:
            hoist_power = -0.25

        elif key_ascii == key_down:
            hoist_power = 0.25

        elif key_ascii == key_grab:
            if R.magnet.energised:
                print("Unlocking connector")
                R.magnet.energised = False
            else:
                print("Locking connector")
                R.magnet.energised = True

        elif key_ascii == key_sense:
            print_sensors(R)

        # Work our way through all the enqueued key presses before dropping
        # out to the timestep
        key = keyboard.getKey()

    if boost:
        # double power values but constrain to [-1, 1]
        bridge_power = max(min(bridge_power * 2, 1), -1)
        trolley_power = max(min(trolley_power * 2, 1), -1)
        hoist_power = max(min(hoist_power * 2, 1), -1)

    R.motor_boards[0].motors[0].power = bridge_power
    R.motor_boards[0].motors[1].power = trolley_power
    R.motor_boards[1].motors[0].power = hoist_power

    R.sleep(KEYBOARD_SAMPLING_PERIOD / 1000)
