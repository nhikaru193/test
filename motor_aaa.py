from motor import MotorDriver
import RPi.GPIO as GPIO
import time

driver = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,   # 左モーター用（モータA）
    PWMB=19, BIN1=16, BIN2=26,   # 右モーター用（モータB）
    STBY=21                      # STBYピン
)

driver.changing_forward(0, 20)

driver.changing_forward(20, 30)

driver.changing_forward(30, 40)

driver.changing_forward(50, 70)

print("加速終了")

time.sleep(2)

driver.changing_forward(70, 0)

GPIO.cleanup()
print("GPIOのクリーンアップを実行しました。")
