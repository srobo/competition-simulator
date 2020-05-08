
# The maximum value that the motor board will accept
SPEED_MAX = 100
MOTOR_NAMES = ["M1","M2","M3"]#,"M4"]

def get_motor_id(board, channel):
    return MOTOR_NAMES[(board*2)+channel]

def init_motor_array(webot):
    return [Motor(0, webot), Motor(1, webot)]

class Motor(object):
    """A motor"""
    def __init__(self, board_id, webot):
        self.board_id = board_id
        self.m0 = MotorChannel(0, webot, board_id)
        self.m1 = MotorChannel(1, webot, board_id)
        self.webot = webot
        self.initialise_webot_motors()

    def initialise_webot_motors(self):
        for m in MOTOR_NAMES:
            self.webot.getMotor(m).setPosition(float('inf'))
            self.webot.getMotor(m).setVelocity(float(0))

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

        # Limit the value to within the valid range
        if value > SPEED_MAX:
            value = SPEED_MAX
        elif value < -SPEED_MAX:
            value = -SPEED_MAX

        motor_id = get_motor_id(self.board_id, self.channel)
        print("motor: "+motor_id+ ". speed: "+str(value))
        motor = self.webot.getMotor(motor_id)
        motor.setVelocity(value)

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