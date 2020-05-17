from collections import OrderedDict
from sr.robot.randomizer import add_jitter

# The maximum value that the motor board will accept
SPEED_MAX = 100
ROTATIONAL = "R"
LINEAR = "L"
MOTOR_NAMES = OrderedDict()#{:ROTATIONAL,'M2':ROTATIONAL,:LINEAR, :LINEAR,:LINEAR}
MOTOR_NAMES['left wheel'] = ROTATIONAL
MOTOR_NAMES['right wheel'] = ROTATIONAL
MOTOR_NAMES['lift motor'] = LINEAR
MOTOR_NAMES['left finger motor'] = LINEAR
MOTOR_NAMES['right finger motor'] = LINEAR

def get_motor_id(board, channel):
    return list(MOTOR_NAMES.keys())[(board*2)+channel]

def init_motor_array(webot):
    return [Motor(0, webot), Motor(1, webot)]

def translate(sr_speed_val, motor):
    # Translate from -100 to 100 range to the actual motor control range

    # Set the speed ranges
    in_from = -SPEED_MAX
    in_to = SPEED_MAX
    out_from = -motor.getMaxVelocity()
    out_to = motor.getMaxVelocity()

    if sr_speed_val != 0:
        #print "Requested: " + str(sr_speed_val)
        sr_speed_val = add_jitter(sr_speed_val, -SPEED_MAX, SPEED_MAX)
        #print "Actual: " + str(sr_speed_val)

    out_range = out_to - out_from
    in_range = in_to - in_from
    in_val = sr_speed_val - in_from
    val=(float(in_val)/in_range)*out_range
    out_val = out_from+val
    return out_val

class Motor(object):
    """A motor"""
    def __init__(self, board_id, webot):
        self.board_id = board_id
        self.m0 = MotorChannel(0, webot, board_id)
        self.m1 = MotorChannel(1, webot, board_id)
        self.webot = webot
        self.initialise_webot_motors()

    def initialise_webot_motors(self):
        for m in MOTOR_NAMES.keys():
            current_motor = self.webot.getMotor(m)
            if current_motor != None:
                if MOTOR_NAMES.get(m) == ROTATIONAL:
                    current_motor.setPosition(float('inf'))
                    current_motor.setVelocity(float(0))
                elif MOTOR_NAMES.get(m) == LINEAR:
                    current_motor.setPosition(float(0))
                    current_motor.setVelocity(float(0))

class MotorChannel(object):
    def __init__(self, channel, webot, board_id):
        self.channel = channel
        self.webot = webot
        self.board_id = board_id
        # Private shadow of use_brake
        #self._use_brake = True # TODO create new thread for non-braking slowdown

        # There is currently no method for reading the power from a motor board
        self._power = 0

    @property
    def power(self):
        return self._power

    @power.setter
    def power(self, value):
        "target setter function"
        value = int(value)
        self._power = value

        motor_id = get_motor_id(self.board_id, self.channel)
        motor = self.webot.getMotor(motor_id)

        # Limit the value to within the valid range
        if value > SPEED_MAX:
            value = SPEED_MAX
        elif value < -SPEED_MAX:
            value = -SPEED_MAX

        print("Setting speed of " + str(motor_id) + " to " + str(value))

        if MOTOR_NAMES.get(motor.getName()) == ROTATIONAL:
            motor.setVelocity(translate(value, motor))
        elif MOTOR_NAMES.get(motor.getName()) == LINEAR:
            motor.setVelocity(0)
            if value < 0:
                motor.setPosition(motor.getMinPosition())
            else:
                motor.setPosition(motor.getMaxPosition())
            motor.setVelocity(abs(translate(value, motor)))
        #motor.setVelocity(translate(value, motor))

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
