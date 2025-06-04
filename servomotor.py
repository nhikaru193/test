import RPi.GPIO as GPIO
import time

SERVO_PIN = 18  # BCM番号で指定（ピン12）

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# 50Hz の PWM（サーボ用）
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def set_servo_duty(duty):
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)

try:
    print("正転（ゆっくり）")
    set_servo_duty(7.5)  # 約1.5ms → 停止（個体により動くかも）

    time.sleep(2)

    print("正転（速い）")
    set_servo_duty(10.0)  # 約2.0ms

    time.sleep(2)

    print("逆転（速い）")
    set_servo_duty(5.0)  # 約1.0ms

    time.sleep(2)

    print("停止")
    set_servo_duty(7.5)

finally:
    pwm.stop()
    GPIO.cleanup()
