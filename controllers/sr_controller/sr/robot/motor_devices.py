from abc import ABC, abstractmethod


class MotorBase(ABC):
    def __init__(self, webot, motor_name):
        self.__webot_motor = webot.getMotor(motor_name)
        self._max_speed = self.__webot_motor.getMaxVelocity()

    @abstractmethod
    def set_speed(self, speed):
        pass


class Wheel(MotorBase):

    def __init__(self, webot, motor_name):
        super().__init__(webot, motor_name)
        self.__webot_motor.setPosition(float('inf'))
        self.__webot_motor.setVelocity(0)

    def set_speed(self, speed):
        self.__webot_motor.setVelocity(speed)


class LinearMotor(MotorBase):

    def __init__(self, webot, motor_name):
        super().__init__(webot, motor_name)
        self.__webot_motor.setPosition(0)
        self.__webot_motor.setVelocity(0)

    def set_speed(self, speed):
        motor = self.__webot_motor
        if speed < 0:
            motor.setPosition(motor.getMinPosition())
        else:
            motor.setPosition(motor.getMaxPosition())
        motor.setVelocity(abs(speed))


class Gripper(MotorBase):

    def __init__(self, webot, motor_1_name, motor_2_name):
        self.gripper_motors = [
            LinearMotor(webot, motor_1_name),
            LinearMotor(webot, motor_2_name),
        ]
        self._max_speed = self.gripper_motors[0]._max_speed

    def set_speed(self, speed):
        for motor in self.gripper_motors:
            motor.set_speed(speed)
