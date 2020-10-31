from typing import Tuple

from controller import Robot


class MotorBase:
    """
    A base class for any type of motor as these are common attributes
    """

    def __init__(self, webot: Robot, motor_name: str) -> None:
        self.motor_name = motor_name
        self.webot_motor = webot.getMotor(motor_name)
        self.max_speed = self.webot_motor.getMaxVelocity()


class Wheel(MotorBase):
    """
    A standard rotational motor in Webots
    """

    def __init__(self, webot: Robot, motor_name: str) -> None:
        super().__init__(webot, motor_name)
        self.webot_motor.setPosition(float('inf'))
        self.webot_motor.setVelocity(0)

    def set_speed(self, speed: float) -> None:
        self.webot_motor.setVelocity(speed)


class LinearMotor(MotorBase):
    """
    A standard linear motor in Webots
    """

    def __init__(self, webot: Robot, motor_name: str) -> None:
        super().__init__(webot, motor_name)
        self.webot_motor.setPosition(0)
        self.webot_motor.setVelocity(0)

    def set_speed(self, speed: float) -> None:
        motor = self.webot_motor
        if speed < 0:
            motor.setPosition(motor.getMinPosition() + 0.01)
        else:
            motor.setPosition(motor.getMaxPosition())
        motor.setVelocity(abs(speed))


class Gripper(MotorBase):
    """
    Our default robot's gripper has its fingers attached to linear motors.
    This class allows you to control these as a single entity to open/close.

    You should initialise with the motor_name as the two Webots motor names separated by
    a pipe character (|)
    """

    def __init__(self, webot: Robot, motor_names: Tuple[str, str]) -> None:
        self.webot = webot
        self.gripper_motors = [
            LinearMotor(self.webot, name) for name in motor_names
        ]
        self.max_speed = self.gripper_motors[0].max_speed

    def set_speed(self, speed: float) -> None:
        for motor in self.gripper_motors:
            motor.set_speed(speed)
