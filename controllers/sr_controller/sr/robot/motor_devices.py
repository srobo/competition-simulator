class MotorBase(object):
    def __init__(self, webot, motor_name):
        self.webot = webot
        self.motor_name = motor_name
        self.webot_motor = self.webot.getMotor(motor_name)
        if self.webot_motor is None:
            return
        self.max_speed = self.webot_motor.getMaxVelocity()

    def _set_speed(self, speed):
        if self.webot_motor is None:
            return


class Wheel(MotorBase):

    def __init__(self, webot, motor_name):
        super().__init__(webot, motor_name)
        self.webot_motor.setPosition(float('inf'))
        self.webot_motor.setVelocity(0)

    def set_speed(self, speed):
        self._set_speed(speed)
        self.webot_motor.setVelocity(speed)


class LinearMotor(MotorBase):

    def __init__(self, webot, motor_name):
        super().__init__(webot, motor_name)
        self.webot_motor.setPosition(0)
        self.webot_motor.setVelocity(0)

    def set_speed(self, speed):
        self._set_speed(speed)
        motor = self.webot_motor
        if speed < 0:
            motor.setPosition(motor.getMinPosition())
        else:
            motor.setPosition(motor.getMaxPosition())
        motor.setVelocity(abs(speed))


class Gripper(MotorBase):

    def __init__(self, webot, motor_name):
        self.webot = webot
        names = motor_name.split("|")
        self.gripper_motors = [
            LinearMotor(self.webot, names[0]),
            LinearMotor(self.webot, names[1]),
        ]
        self.max_speed = self.gripper_motors[0].max_speed

    def set_speed(self, speed):
        for motor in self.gripper_motors:
            motor.set_speed(speed)
