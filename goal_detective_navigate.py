#goalyudo_nocamera.py→color_detective_navigate.py→このファイル
import cv2
import math
import time
import RPi.GPIO as GPIO
from motor import MotorDriver
from picamera2 import Picamera2
import numpy as np

#コーン、ボールを一定割合以上検知し、静止している状態からのスタート
#ARLISSゴール付近のボールは大きさが既知であるため検知割合による距離の計算が可能

#モータの初期化
driver = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,   # 左モーター用（モータA）
    PWMB=19, BIN1=16, BIN2=26,   # 右モーター用（モータB）
    STBY=21                      # STBYピン
)

# カメラ初期化と設定
picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (320, 240)})
picam2.configure(config)
picam2.start()
time.sleep(1)

#速度定義
Va = 0
Vb = 0

#関数定義(画像取得→画像処理→hsv変換→面積計算→割合計算)　戻り値はpercentage(画像赤色検知割合)
def get_percentage():
    frame = picam2.capture_array()
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 30, 30])
    upper_red1 = np.array([20, 255, 255])
    lower_red2 = np.array([95, 30, 30])
    upper_red2 = np.array([130, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    red_area = np.count_nonzero(mask)
    total_area = frame.shape[0] * frame.shape[1]
    percentage = (red_area / total_area) * 100
    return percentage

def get_block_number():
    number = None
    frame = picam2.capture_array()
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 30, 30])
    upper_red1 = np.array([20, 255, 255])
    lower_red2 = np.array([95, 30, 30])
    upper_red2 = np.array([130, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])  # x座標の重心
            width = frame.shape[1]
            w = width // 5  # 5分割幅
            if cx < w:
                number = 1
            elif cx < 2 * w:
                number = 2
            elif cx < 3 * w:
                number = 3
            elif cx < 4 * w:
                number = 4
            else:
                number = 5
        else:
            print("⚠️ 重心が計算できません")
    else:
        print("❌ 赤色物体が見つかりません")
    return number

def distance(percentage)
    x = (320 * 240 * percentage) / 3.141592
    mother = sqrt(x)
    distance = 824 * 0.20 / mother
    return distance

"""
number = get_block_number()
print(number)
"""
try: 
    #まずはゴールの正方形内部に入る！
    for i in range(3):
        while true:
            driver.changing_left(0, 10)
            driver.changing_left(10, 0)
            number = get_block_number()
            if number == 3:
                Vb = 40
                Vb = Vb - i * 10
                driver.changing_forward(0, Vb)
                driver.changing_forward(Vb, 0)
                break
        driver.motor_stop_free()

    #次は中心地を求める
    r1 = r2 = r3 = r4 = s1 = s2 = s3 = s4 = none

    #r[m], s[rad]
    while true:
        driver.changing_left(0, 10)
        driver.changing_left(10, 0)
        number = get_block_number()
            if number == 3:
                percentage = get percentage()
                
                
    
   
        


