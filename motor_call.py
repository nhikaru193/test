import RPi.GPIO as GPIO
from motor import MotorDriver  # motor.py から MotorDriver クラスを読み込む
import time

# モータードライバのインスタンスを作成（仮のピン番号）
driver = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,
    PWMB=19, BIN1=16, BIN2=26,
    STBY=21
)

try:
    print("前進（加速）")
    driver.changing_forward(0, 80)

    time.sleep(2)

    print("前進（減速）")
    driver.changing_forward(80, 0)

finally:
    print("停止")
    driver.cleanup()
