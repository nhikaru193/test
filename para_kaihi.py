#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import pigpio
import board
import busio
import adafruit_bno055
import RPi.GPIO as GPIO
import numpy as np
import cv2
from picamera2 import Picamera2

# -------------------------------
# GPIO モーター制御設定
# -------------------------------
IN1, IN2, IN3, IN4 = 17, 18, 22, 23

def init_motor():
    GPIO.setup(IN1, GPIO.OUT)
    GPIO.setup(IN2, GPIO.OUT)
    GPIO.setup(IN3, GPIO.OUT)
    GPIO.setup(IN4, GPIO.OUT)

def forward():
    GPIO.output(IN1, True)
    GPIO.output(IN2, False)
    GPIO.output(IN3, True)
    GPIO.output(IN4, False)

def turn_left():
    GPIO.output(IN1, False)
    GPIO.output(IN2, True)
    GPIO.output(IN3, True)
    GPIO.output(IN4, False)

def turn_right():
    GPIO.output(IN1, True)
    GPIO.output(IN2, False)
    GPIO.output(IN3, False)
    GPIO.output(IN4, True)

def stop():
    GPIO.output(IN1, False)
    GPIO.output(IN2, False)
    GPIO.output(IN3, False)
    GPIO.output(IN4, False)

def cleanup_motor():
    stop()

# -------------------------------
# GPS (pigpio)
# -------------------------------
RX_PIN = 27
pi = pigpio.pi()
pi.bb_serial_read_open(RX_PIN, 9600, 8)

def convert_to_decimal(coord, direction):
    degrees = int(coord[:2]) if direction in ['N', 'S'] else int(coord[:3])
    minutes = float(coord[2:]) if direction in ['N', 'S'] else float(coord[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

def get_current_location():
    timeout = time.time() + 5
    while time.time() < timeout:
        (count, data) = pi.bb_serial_read(RX_PIN)
        if count and data:
            try:
                text = data.decode("ascii", errors="ignore")
                if "$GNRMC" in text:
                    for line in text.split("\n"):
                        if "$GNRMC" in line:
                            parts = line.strip().split(",")
                            if len(parts) > 6 and parts[2] == "A":
                                lat = convert_to_decimal(parts[3], parts[4])
                                lon = convert_to_decimal(parts[5], parts[6])
                                return lat, lon
            except:
                continue
        time.sleep(0.1)
    raise TimeoutError("GPSデータの取得に失敗しました")

# -------------------------------
# 方位計算（GPS→目的地）
# -------------------------------
def calculate_heading(current_lat, current_lon, dest_lat, dest_lon):
    import math
    delta_lon = math.radians(dest_lon - current_lon)
    y = math.sin(delta_lon) * math.cos(math.radians(dest_lat))
    x = math.cos(math.radians(current_lat)) * math.sin(math.radians(dest_lat)) - \
        math.sin(math.radians(current_lat)) * math.cos(math.radians(dest_lat)) * math.cos(delta_lon)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

# -------------------------------
# 赤色検出（Picamera2 + OpenCV）
# -------------------------------
def detect_red_object(picam2):
    frame = picam2.capture_array()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 120, 70])
    upper_red = np.array([10, 255, 255])
    mask = cv2.inRange(hsv, lower_red, upper_red)
    if np.sum(mask) > 5000:
        return True
    return False

def save_image(frame):
    # 現在の時刻をファイル名に使用
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"photo_{timestamp}.jpg"  # カレントディレクトリに保存
    success = cv2.imwrite(filename, frame)
    if success:
        print(f"画像保存成功: {filename}")
    else:
        print("画像保存に失敗しました。")


# -------------------------------
# 初期化
# -------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
init_motor()

# BNO055（方位センサー）
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)

# Picamera2 設定
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()
time.sleep(2)

# 目的地座標（例：東京駅）
destination_lat = 35.681236
destination_lon = 139.767125

# -------------------------------
# メイン処理
# -------------------------------
try:
    current_lat, current_lon = get_current_location()
    print("現在地：", current_lat, current_lon)

    target_heading = calculate_heading(current_lat, current_lon, destination_lat, destination_lon)
    print("目標方位：", target_heading)

    heading = sensor.euler[0]
    if heading is None:
        heading = 0
    print("現在の方位：", heading)

    diff = (target_heading - heading + 360) % 360
    if 10 < diff < 180:
        print("右旋回")
        turn_right()
    elif diff >= 180:
        print("左旋回")
        turn_left()
    else:
        print("方位OK")
        stop()

    time.sleep(2)

    # 画像キャプチャ
    frame = picam2.capture_array()
    save_image(frame)  # 撮影した画像を保存

    if detect_red_object(picam2):
        print("赤色検出 → 右へ回避")
        turn_right()
        time.sleep(1)
    else:
        print("赤なし → 前進")
        forward()
        time.sleep(2)

    stop()

finally:
    print("終了処理中...")
    cleanup_motor()
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    picam2.close()
    GPIO.cleanup()
    print("全ての処理を終了しました。")
