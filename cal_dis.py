import cv2
import math
import time
import RPi.GPIO as GPIO
from motor import MotorDriver
from picamera2 import Picamera2
import numpy as np

driver = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,
    PWMB=19, BIN1=16, BIN2=26,
    STBY=21
)

picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (320, 240)})
picam2.configure(config)
picam2.start()
time.sleep(1)

REAL_BALL_DIAMETER_CM = 20  # ボールの実直径(cm)
FOCAL_LENGTH_PX = 800       # 焦点距離(px)、実測値に合わせて調整してください

def get_red_mask(frame):
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 30, 30])
    upper_red1 = np.array([20, 255, 255])
    lower_red2 = np.array([95, 30, 30])
    upper_red2 = np.array([130, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    return mask

def get_ball_diameter_px():
    frame = picam2.capture_array()
    mask = get_red_mask(frame)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        (_, _), radius = cv2.minEnclosingCircle(largest)
        diameter_px = radius * 2
        return diameter_px
    else:
        print("❌ 赤色のボールが見つかりません")
        return None

def get_distance_from_diameter(diameter_px):
    if diameter_px is None or diameter_px == 0:
        return None
    distance_cm = (REAL_BALL_DIAMETER_CM * FOCAL_LENGTH_PX) / diameter_px
    return distance_cm

# もし必要なら割合計算も残す
def get_percentage():
    frame = picam2.capture_array()
    mask = get_red_mask(frame)
    red_area = np.count_nonzero(mask)
    total_area = frame.shape[0] * frame.shape[1]
    percentage = (red_area / total_area) * 100
    return percentage

def get_picture():
    image_path = "/home/mark1/Pictures/got_image.jpg"
    picam2.capture_file(image_path)

# --- メイン処理例 ---
diameter_px = get_ball_diameter_px()
print("ボールの直径(px):", diameter_px)

distance = get_distance_from_diameter(diameter_px)
if distance is not None:
    print(f"推定距離: {distance:.2f} cm")
else:
    print("距離の推定に失敗しました")

percentage = get_percentage()
print(f"赤色検出割合: {percentage:.2f} %")

get_picture()
