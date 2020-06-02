from sr.robot.utils import map_to_range
from sr.robot.randomizer import add_jitter
from sr.robot.motor_devices import Wheel, Gripper, LinearMotor

# The maximum value that the motor board will accept
SPEED_MAX = 100


def init_motor_array(webot):
    return [
        Motor([
            Wheel(webot, 'left wheel'),
            Wheel(webot, 'right wheel'),
        ]),
        Motor([
            LinearMotor(webot, 'lift motor'),
            Gripper(webot, 'left finger motor', 'right finger motor'),
        ]),
    ]


def translate(sr_speed_val, sr_motor):
    # Translate from -100 to 100 range to the actual motor control range

    if sr_speed_val != 0:
        sr_speed_val = add_jitter(sr_speed_val, -SPEED_MAX, SPEED_MAX)

    return map_to_range(
        -SPEED_MAX,
        SPEED_MAX,
        -sr_motor._max_speed,
        sr_motor._max_speed,
        sr_speed_val,
    )


class Motor(object):
    """A motor"""

    def __init__(self, sr_motors):
        self.m0 = MotorChannel(sr_motors[0])
        self.m1 = MotorChannel(sr_motors[1])


class MotorChannel(object):
    def __init__(self, sr_motor):
        # Private shadow of use_brake
        # self._use_brake = True # TODO create new thread for non-braking slowdown

        # There is currently no method for reading the power from a motor board
        self._power = 0
        self._sr_motor = sr_motor

    @property
    def power(self):
        return self._power

    @power.setter
    def power(self, value):
        "target setter function"
        value = int(value)
        self._power = value

        # Limit the value to within the valid range
        if value > SPEED_MAX:
            value = SPEED_MAX
        elif value < -SPEED_MAX:
            value = -SPEED_MAX

        self._sr_motor.set_speed(translate(value, self._sr_motor))

    ''''@property
    def use_brake(self):
        "Whether to use the brake when at 0 speed"
        return self._use_brake

    @use_brake.setter
    def use_brake(self, value):
        self._use_brake = value

        if self.power == 0:
            "Implement the new braking setting"
            self.power = 0'''
