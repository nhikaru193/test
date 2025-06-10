import RPi.GPIO as GPIO
from motor import MotorDriver  # motor.py から MotorDriver クラスを読み込む
import time

# インスタンス生成：GPIOピン番号を正しく指定
driver = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,   # 左モーター用（モータA）
    PWMB=19, BIN1=16, BIN2=26,   # 右モーター用（モータB）
    STBY=21                      # STBYピン
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
