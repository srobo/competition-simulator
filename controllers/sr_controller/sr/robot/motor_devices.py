class MotorBase(object):
    def __init__(self, webot):
        self.webot = webot
        
    def initialise_motor(self, motor_name):
        self.motor_name = motor_name
        self.webot_motor = self.webot.getMotor(motor_name)
        if self.webot_motor == None:
            return
        self.max_speed = self.webot_motor.getMaxVelocity()

    def set_speed(self, speed):
        if self.webot_motor == None:
            return

class Wheel(MotorBase):      

    def initialise_motor(self, motor_name):
        super().initialise_motor(motor_name)
        self.webot_motor.setPosition(float('inf'))
        self.webot_motor.setVelocity(float(0))

    def set_speed(self, speed):
        super().set_speed(speed)
        self.webot_motor.setVelocity(speed)

class LinearMotor(MotorBase):

    def initialise_motor(self, motor_name):
        super().initialise_motor(motor_name)
        self.webot_motor.setPosition(0)
        self.webot_motor.setVelocity(0)

    def set_speed(self, speed):
        super().set_speed(speed)
        motor = self.webot_motor
        if speed < 0:
            motor.setPosition(motor.getMinPosition())
        else:
            motor.setPosition(motor.getMaxPosition())
        motor.setVelocity(abs(speed))

class Gripper(MotorBase):

    def initialise_motor(self, motor_name):
        names = motor_name.split("|")
        self.gripper_motors = [LinearMotor(self.webot), LinearMotor(self.webot)]
        for i in range(0, len(self.gripper_motors)):
            self.gripper_motors[i].initialise_motor(names[i])
        self.max_speed = self.gripper_motors[0].max_speed

        
    def set_speed(self, speed):
        for motor in self.gripper_motors:
            motor.set_speed(speed)

        
