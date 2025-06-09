import time
from motor import MotorDriver

MotorDriver.__init__(self,
                  PWMA, AIN1, AIN2,
                  PWMB, BIN1, BIN2, STBY,
                  freq = 1000):

  print("前進加速中")
  MotorDriver.changing_forward(0, 80)
  
  print("前進減速中")
  MotorDriver.changing_forward(80, 0)
  
  print("右折加速中")
  MotorDriver.changing_right(0, 50)
  
  print("右折減速中")
  MotorDriver.changing_right(50, 0)
