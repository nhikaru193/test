import RPi.GPIO as GPIO
import time
import smbus
import struct
from motor import MotorDriver

motor = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,   # 左モーター用（モータA）
    PWMB=19, BIN1=16, BIN2=26,   # 右モーター用（モータB）
    STBY=21                      # STBYピン
)

motor.changing_forwardd(0, 100, 0.90)
print("加速完了です。地上に置いてください")
time.sleep(10)
print("減速開始します")
motor.changing_forwardd(100, 0, 0.90)

motor.cleanup()

