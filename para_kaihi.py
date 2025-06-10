import time
import RPi.GPIO as GPIO
from GNSS_navigate import direction
from GNSS_navigate import distance
import cv2
import numpy as np
from smbus2 import SMBus
from bno055 import BNO055

# GPIOの初期化
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# モーター初期化
motor = init()

# BNO055初期化
bus = SMBus(1)
bno = BNO055(i2c_bus=bus)
if not bno.begin():
    raise RuntimeError("BNO055の初期化に失敗しました")

# カメラ初期化
camera = cv2.VideoCapture(0)

# 目的地の座標（例）
destination_lat = 35.681236
destination_lon = 139.767125

def calculate_heading(current_lat, current_lon, dest_lat, dest_lon):
    import math
    delta_lon = math.radians(dest_lon - current_lon)
    y = math.sin(delta_lon) * math.cos(math.radians(dest_lat))
    x = math.cos(math.radians(current_lat)) * math.sin(math.radians(dest_lat)) - \
        math.sin(math.radians(current_lat)) * math.cos(math.radians(dest_lat)) * math.cos(delta_lon)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

def detect_color():
    ret, frame = camera.read()
    if not ret:
        return None

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # 例: 赤色の範囲
    lower_red = np.array([0, 120, 70])
    upper_red = np.array([10, 255, 255])
    mask = cv2.inRange(hsv, lower_red, upper_red)

    if np.sum(mask) > 5000:  # 閾値調整
        return "red"
    return None

try:
    # 初期位置取得
    current_lat, current_lon = direction()
    target_heading = calculate_heading(current_lat, current_lon, destination_lat, destination_lon)

    # 現在の方位取得
    heading = bno.read_euler()[0]  # Yaw

    # 方位修正
    diff = (target_heading - heading + 360) % 360
    if diff > 10 and diff < 180:
        motor.turn_right()
    elif diff >= 180:
        motor.turn_left()
    else:
        motor.stop()

    time.sleep(2)  # 方位修正の待機

    # 色検出
    color = detect_color()
    if color == "red":
        motor.turn_right()
        time.sleep(1)
    else:
        motor.forward()
        time.sleep(2)

    # 再度GPS取得し、停止
    current_lat, current_lon = get_current_location()
    motor.stop()

    # キャリブレーション処理（例：IMUリセット）
    bno.set_mode(BNO055.OPERATION_MODE_CONFIG)
    time.sleep(1)
    bno.set_mode(BNO055.OPERATION_MODE_NDOF)
    print("キャリブレーション完了")

finally:
    motor.cleanup()
    camera.release()
    GPIO.cleanup()
