import socket
import selectors
from typing import Tuple, Optional

from sr.robot import Robot
from controller import Keyboard

s = socket.socket(
    socket.AF_INET6,
    socket.SOCK_STREAM,
    socket.SOL_TCP,
)
s.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1,
)

s.bind(('::', 8000))

s.listen(1)

conn, _ = s.accept()

sel = selectors.DefaultSelector()
sel.register(conn, selectors.EVENT_READ)


# Any keys still pressed in the following period will be handled again
# leading to repeated claim attempts or printing sensors multiple times
KEYBOARD_SAMPLING_PERIOD = 100
NO_KEY_PRESSED = -1

CONTROLS = {
    "forward": (ord("W"), ord("I")),
    "reverse": (ord("S"), ord("K")),
    "left": (ord("A"), ord("J")),
    "right": (ord("D"), ord("L")),
    "claim": (ord("E"), ord("O")),
    "sense": (ord("Q"), ord("U")),
    "scan": (ord("R"), ord("P")),
    "boost": (Keyboard.SHIFT, Keyboard.CONTROL),
}


def print_sensors(robot: Robot) -> None:
    distance_sensor_names = [
        "Front Left",
        "Front Right",
        "Left",
        "Right",
        "Back Left",
        "Back Right",
    ]
    touch_sensor_names = [
        "Front",
        "Rear",
    ]

    print(f"Distance sensor readings at {robot.time():.2f}s:")
    for pin, name in enumerate(distance_sensor_names):
        dist = R.ruggeduinos[0].analogue_read(pin)
        print(f"{pin} {name: <12}: {dist:.2f}")

    print("Touch sensor readings:")
    for pin, name in enumerate(touch_sensor_names, 2):
        touching = R.ruggeduinos[0].digital_read(pin)
        print(f"{pin} {name: <6}: {touching}")

    print()


R = Robot()

keyboard = Keyboard()
keyboard.enable(KEYBOARD_SAMPLING_PERIOD)

pending_claims = []

key_forward = chr(CONTROLS["forward"][R.zone])
key_reverse = chr(CONTROLS["reverse"][R.zone])
key_left = chr(CONTROLS["left"][R.zone])
key_right = chr(CONTROLS["right"][R.zone])
key_claim = chr(CONTROLS["claim"][R.zone])
key_sense = chr(CONTROLS["sense"][R.zone])
key_scan = chr(CONTROLS["scan"][R.zone])
key_boost = CONTROLS["boost"][R.zone]

print(
    "Note: you need to click on 3D viewport for keyboard events to be picked "
    "up by webots",
)


def get_key_from_socket() -> Optional[Tuple[str, bool]]:
    events = sel.select(timeout=0.001)
    if events:
        key = conn.recv(1).decode()
        return key.upper(), key.isupper()
    return None


def get_key_from_keyboard() -> Optional[Tuple[str, bool]]:
    key = keyboard.getKey()

    if key == NO_KEY_PRESSED:
        return None

    key_ascii = key & 0x7F  # mask out modifier keys
    # note: modifiers are only recorded when pressed before other keys
    key_mod = key & (~0x7F)

    return chr(key_ascii), key_mod == key_boost


def get_key() -> Optional[Tuple[str, bool]]:
    key = get_key_from_socket()
    if key:
        return key

    return get_key_from_keyboard()


while True:
    key = get_key()

    boost = False

    left_power = 0
    right_power = 0

    while key is not None:
        key_ascii, boost = key

        if key_ascii == key_forward:
            left_power += 50
            right_power += 50

        elif key_ascii == key_reverse:
            left_power += -50
            right_power += -50

        elif key_ascii == key_left:
            left_power -= 25
            right_power += 25

        elif key_ascii == key_right:
            left_power += 25
            right_power -= 25

        elif key_ascii == key_claim:
            R.radio.begin_territory_claim()
            pending_claims.append(R.time() + 2)

        elif key_ascii == key_sense:
            print_sensors(R)

        elif key_ascii == key_scan:
            transmitters = R.radio.sweep()
            print("Found transmitter(s)")

            for transmitter in transmitters:
                print(transmitter)

            print()

        # Work our way through all the enqueued key presses before dropping
        # out to the timestep
        key = get_key()

    if boost:
        # double power values but constrain to [-100, 100]
        left_power = max(min(left_power * 2, 100), -100)
        right_power = max(min(right_power * 2, 100), -100)

    R.motors[0].m0.power = left_power
    R.motors[0].m1.power = right_power

    current_time = R.time()
    # complete claims after their 2 seconds has lapsed
    for claim_end_time in pending_claims:
        if current_time > claim_end_time:
            R.radio.complete_territory_claim()
            pending_claims.remove(claim_end_time)

    R.sleep(KEYBOARD_SAMPLING_PERIOD / 1000)
