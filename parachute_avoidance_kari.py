import time
import cv2
import numpy as np
from datetime import datetime
from picamera2 import Picamera2
from motor import MotorDriver
import RPi.GPIO as GPIO

# BNO055関連
import board
import busio
import adafruit_bno055

# GPS関連（pigpio使用）
import pigpio

# === BNO055 初期化 ===
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)

def get_heading():
    heading = sensor.euler[0]
    return heading if heading is not None else 0

def rotate_to_direction(target_heading, motor, tolerance=5, speed=50):
    while True:
        current_heading = get_heading()
        diff = (target_heading - current_heading + 360) % 360
        if diff < tolerance or diff > (360 - tolerance):
            motor.motor_stop_free()
            print(f"✅ 方角 {target_heading}° に到達（現在: {current_heading:.1f}°）")
            break
        if diff > 180:
            motor.motor_left(speed)
        else:
            motor.motor_right(speed)
        time.sleep(0.1)

# === GPS関連関数 ===
TX_PIN = 17
RX_PIN = 27
BAUD = 9600

def convert_to_decimal(coord, direction):
    if not coord or not direction:
        return None
    degrees = int(coord[:2]) if direction in ['N', 'S'] else int(coord[:3])
    minutes = float(coord[2:]) if direction in ['N', 'S'] else float(coord[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

def read_gps_once():
    pi = pigpio.pi()
    if not pi.connected:
        print("pigpio に接続できません")
        return None
    if pi.bb_serial_read_open(RX_PIN, BAUD, 8) != 0:
        print("ソフトUARTの初期化に失敗")
        pi.stop()
        return None

    timeout = time.time() + 5  # 5秒でタイムアウト
    try:
        while time.time() < timeout:
            count, data = pi.bb_serial_read(RX_PIN)
            if count and data:
                text = data.decode("ascii", errors="ignore")
                if "$GNRMC" in text:
                    lines = text.split("\n")
                    for line in lines:
                        if "$GNRMC" in line:
                            parts = line.strip().split(",")
                            if len(parts) > 6 and parts[2] == "A":
                                lat = convert_to_decimal(parts[3], parts[4])
                                lon = convert_to_decimal(parts[5], parts[6])
                                pi.bb_serial_read_close(RX_PIN)
                                pi.stop()
                                return lat, lon
            time.sleep(0.1)
    finally:
        pi.bb_serial_read_close(RX_PIN)
        pi.stop()

    return None

# === 赤色検出関数 ===
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

# === 初期化 ===
image_path = "/home/pi/Pictures/para.jpg"

camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()
time.sleep(2)

motor = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,
    PWMB=19, BIN1=16, BIN2=26,
    STBY=21
)

# === メインループ ===
try:
    while True:
        gps = read_gps_once()
        if gps:
            lat, lon = gps
            print(f"📍 GPS取得: 緯度 {lat:.6f}, 経度 {lon:.6f}")
            target_direction = 90  # 仮に東方向
            rotate_to_direction(target_direction, motor)
        else:
            print("⚠️ GPS取得失敗")

        camera.capture_file(image_path)
        print(f"📸 撮影完了: {image_path}")

        if is_red_detected(image_path):
            print("🔴 赤色検出 → 回避行動")
            motor.motor_stop_free()
            time.sleep(0.5)
            motor.motor_right(60)
            time.sleep(1.0)
            motor.motor_forward(60)
            time.sleep(1.5)
            motor.motor_stop_free()
        else:
            print("🟢 赤色なし → 前進")
            motor.motor_forward(60)
            time.sleep(1.5)
            motor.motor_stop_free()

        time.sleep(2)

except KeyboardInterrupt:
    print("❌ 強制終了")

finally:
    motor.cleanup()
    camera.stop()
    print("✅ 正常終了")
