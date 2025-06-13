import time
import cv2
import numpy as np
from datetime import datetime
from picamer2 import PiCamera2
from motor import MotorDriver
import RPi.GPIO as GPIO
import serial

# BNO055関連追加
import board
import busio
import adafruit_bno055

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)  # BNO055_I2Cを使う

def get_heading():
    heading = sensor.euler[0]  # Yaw角度、0-360度
    if heading is None:
        return 0
    return heading

def rotate_to_direction(target_heading, motor, tolerance=5, speed=50):
    """
    目標角度に向くまで回転するシンプル関数
    """
    while True:
        current_heading = get_heading()
        if current_heading is None:
            print("⚠️ BNO055の角度取得失敗")
            time.sleep(0.1)
            continue

        diff = (target_heading - current_heading + 360) % 360
        if diff < tolerance or diff > (360 - tolerance):
            motor.motor_stop_free()
            print(f"✅ 目標方角 {target_heading}°に到達（現在: {current_heading:.1f}°）")
            break

        if diff > 180:
            motor.motor_left(speed)
            print(f"⏪ 左回転 (差: {diff:.1f}° 現在: {current_heading:.1f}°)")
        else:
            motor.motor_right(speed)
            print(f"⏩ 右回転 (差: {diff:.1f}° 現在: {current_heading:.1f}°)")

        time.sleep(0.1)

# === 以下は既存コード ===

def read_gps(serial_port="/dev/ttyUSB0", baudrate=9600, timeout=1):
    # 省略
    pass

def nmea_to_decimal(coord, direction):
    # 省略
    pass

image_dir = "/home/pi/images"
camera = PiCamera()
camera.resolution = (640, 480)

motor = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,
    PWMB=19, BIN1=16, BIN2=26,
    STBY=21
)

def is_red_detected(image_path, threshold=1000):
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0, 70, 50])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([160, 70, 50])
    upper2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)
    red_area = cv2.countNonZero(mask)
    print(f"🔴 赤色面積: {red_area}")
    return red_area > threshold


try:
    while True:
        # GPS取得（例）
        lat, lon = read_gps("/dev/ttyUSB0")
        if lat and lon:
            print(f"📍 GPS取得: 緯度 {lat:.6f}, 経度 {lon:.6f}")
            # ここでlat, lonから目的地の方角を計算するロジックを入れる（省略）
            # 例として仮に目的方向を90度（東）に固定
            target_direction = 90

            # 目的方向に回転させる
            rotate_to_direction(target_direction, motor)

        else:
            print("⚠️ GPS信号なし")

        # 撮影
        image_path = "/home/mark1/Pictures/para.jpg"
        camera.capture(image_path)
        print(f"📸 撮影完了: {image_path}")

        # 赤色検出
        if is_red_detected(image_path):
            print("🔴 赤色を検出 → 回避行動開始")
            motor.motor_stop_free()
            time.sleep(0.5)
            motor.motor_right(60)
            time.sleep(1.0)
            motor.motor_forward(60)
            time.sleep(1.5)
            motor.motor_stop_free()
        else:
            print("🟢 赤なし → 前進")
            motor.motor_forward(60)
            time.sleep(1.5)
            motor.motor_stop_free()

        time.sleep(2)

except KeyboardInterrupt:
    print("❌ 中断されました")

finally:
    motor.cleanup()
    camera.close()
