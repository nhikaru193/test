
import RPi.GPIO as GPIO
import time

SERVO_PIN = 13  # GPIO13を使用

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# 50Hz の PWM波形（サーボ用）
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def set_servo_duty(duty):
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)

try:
    print("サーボ停止")
    set_servo_duty(7.5)

    print("正回転（速い）")
    set_servo_duty(10.0)

    time.sleep(10)

    print("逆回転（速い）")
    set_servo_duty(5.0)

    time.sleep(10)

    print("停止")
    set_servo_duty(7.5)

finally:
    pwm.stop()
    GPIO.cleanup()
