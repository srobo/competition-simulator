class MotorBase(object):
    def __init__(self, webot):
        self.webot = webot
        print("constructed")
        
    def initialise_motor(self, motor_name):
        print("init "+motor_name)
        self.webot_motor = self.webot.getMotor(motor_name)
        if self.webot_motor == None:
            print("Null motor in init")
            return

    def set_speed(self, speed):
        if self.webot_motor == None:
            print("Null motor in set_speed")
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
        self.webot_motor.setPosition(float(0))
        self.webot_motor.setVelocity(float(0))

    def set_speed(self, speed):
        super().set_speed(speed)
        motor = self.webot_motor
        motor.setVelocity(0)
        if speed < 0:
            motor.setPosition(motor.getMinPosition())
        else:
            motor.setPosition(motor.getMaxPosition())
        motor.setVelocity(abs(speed))

class Gripper(MotorBase):

    def initialise_motor(self, motor_name):
        names = motor_name.split("|")
        self.gripper_motors = {LinearMotor(names[0]), LinearMotor(names[1])}

    def set_speed(self, speed):
        for motor in self.gripper_motors:
            motor.set_speed(speed)

        