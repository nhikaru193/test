import cv2
import numpy as np
import time
import A_camera
import smbus
from picamera2 import Picamera2
import struct
#import RPi.GPIO as GPIO
import math
import pigpio

#作成ファイルのインポート
import A_fusing
import A_BME280
import A_following
from A_BNO055 import BNO055
from A_Motor import MotorDriver
from A_Flag_B import Flag_B

#ミッション部分
from A_RE import RD
from A_LD import LD
from A_PA import PA
from A_FN import FN
import A_Servo
from A_exGPS import GPS
from A_GDA import GDA

#初期設定
Flag_location_a = [39.5908982, -119.2345484]
Flag_location_b = [39.5908552, -119.2344582]
Goal_location = [39.5908452, -119.2344096]
t = 1

#BNO055の初期設定
bno = BNO055()
bno.begin()
time.sleep(1)
bno.setMode(BNO055.OPERATION_MODE_NDOF)
time.sleep(1)
bno.setExternalCrystalUse(True)
#GPIO.setmode(GPIO.BCM)

pi = pigpio.pi()
if not pi.connected:
    print("pigpiodデーモンに接続できません。sudo pigpiodを実行してください。")
    exit()

PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY = 12, 23, 18, 19, 16, 26, 21
driver = MotorDriver(pi, PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY)

while True:
    sys, gyro, accel, mag = bno.getCalibration()
    print(f"gyro:{gyro}, mag:{mag}")
    if gyro == 3 and mag == 3:
        print("BNO055のキャリブレーション終了")
        break
    #driver.cleanup()
    time.sleep(0.3)

#ここのタイムスリープは収納待ちのタイムスリープ
time.sleep(t)


RELEASE = RD(bno)
RELEASE.run()

LAND = LD(bno, driver, pi=pi)
LAND.run()

time.sleep(3)

print("パラシュート回避を始めます")
time.sleep(1)

AVOIDANCE = PA(bno, driver, goal_location=Flag_location_a, pi=pi)
AVOIDANCE.run()

GPS_StoE = GPS(bno, driver, goal_location=Flag_location_a, pi=pi)
GPS_StoE.run()

GPS_StoF = GPS(bno, driver, goal_location=Flag_location_b, pi=pi)
GPS_StoF.run()

FLAG = FN(bno, driver, flag_location=Flag_location_b, pi=pi)
FLAG.run()

A_Servo.release()
time.sleep(5)

GPS_FtoG = GPS(bno, driver, goal_location=Goal_location, pi=pi)
GPS_FtoG.run()

GOAL = GDA(bno, driver, pi=pi, counter_max=30)
GOAL.run()

print("Mission Complete")
# プログラムの最後にリソースを解放
driver.cleanup()
pi.stop()
print("Mission Complete")
