import logging

# The maximum value that the motor board will accept
SPEED_MAX = 100

class Motor(object):
    """A motor"""
    def __init__(self):

        self.m0 = MotorChannel(0)
        self.m1 = MotorChannel(1)

class MotorChannel(object):
    def __init__(self, channel):
        self.channel = channel

        # Private shadow of use_brake
        self._use_brake = True

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

        with self.lock:
            # TODO: set motor speed here
            if self.channel == 0:
                self.serial.write(CMD_SPEED0)
            else:
                self.serial.write(CMD_SPEED1)

            if value == 0 and self.use_brake:
                self.serial.write(SPEED_BRAKE)
            else:
                self.serial.write(self._encode_speed(value))

    @property
    def use_brake(self):
        "Whether to use the brake when at 0 speed"
        return self._use_brake

    @use_brake.setter
    def use_brake(self, value):
        self._use_brake = value

        if self.power == 0:
            "Implement the new braking setting"
            self.power = 0
