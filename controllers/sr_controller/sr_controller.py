import time

from sr.robot import *

R = Robot()

while True:
    print("Dist L:", R.ruggeduinos[0].analogue_read(0))
    print("Dist R:", R.ruggeduinos[0].analogue_read(1))
