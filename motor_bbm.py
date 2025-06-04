import RPi.GPIO as GPIO
import time

BIN1 = 16
BIN2 = 26
PWMB = 19
STBY = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup([BIN1, BIN2, PWMB, STBY], GPIO.OUT)

# STBY解除
GPIO.output(STBY, GPIO.HIGH)

pwm = GPIO.PWM(PWMB, 1000)
pwm.start(0)

def motor_forward(speed=50):
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def motor_stop():
    pwm.ChangeDutyCycle(0)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

try:
    print("モーター前進")
    motor_forward(60)
    time.sleep(2)

    print("停止")
    motor_stop()

finally:
    pwm.stop()
    GPIO.cleanup()
