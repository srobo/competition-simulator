class MotorBase(object):
    def __init__(self, webot):
        self.webot = webot

class Wheel(MotorBase):
    def __init__(self, webot):
        super().__init__(webot)

    def set_speed(self, speed):
        

class LinearMotor(MotorBase):
    def __init__(self, webot):
        super().__init__(webot)

class Gripper(MotorBase):
    def __init__(self, webot):
        super().__init__(webot)
        