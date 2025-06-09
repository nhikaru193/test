import time
from motor import MotorDriver

print("前進加速中")
MotorDriver.changing_forward(0, 80)

print("前進減速中")
MotorDriver.changing_forward(80, 0)

print("右折加速中")
MotorDriver.changing_right(0, 50)

print("右折減速中")
MotorDriver.changing_right(50, 0)
