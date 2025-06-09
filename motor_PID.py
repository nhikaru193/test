import RPi.GPIO as GPIO
import time

BIN1 = 16
BIN2 = 26
PWMB = 19
STBY = 21

speed = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup([BIN1, BIN2, PWMB, STBY], GPIO.OUT)

# STBY解除
GPIO.output(STBY, GPIO.HIGH)

pwm = GPIO.PWM(PWMB, 1000)
pwm.start(0)

def motor_any(speed):
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def changing_control(before, after):
   global speed
   for i in range(200):
       delta_speed = (after - before) / 200
       speed = before + i * delta_speed
       motor_any(speed)
       time.sleep(0.01)
     
try:
    a_speed = 0
    b_speed = 80
    changing_control(a_speed, b_speed)
    C_speed = 0 
    changing_control(b_speed, c_speed)
    
finally:
    pwm.stop()
    GPIO.cleanup()
