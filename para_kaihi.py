#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import pigpio
import cv2
import numpy as np
import board
import busio
import adafruit_bno055
import RPi.GPIO as GPIO

# -------------------------------
# モーター制御設定
# -------------------------------
IN1 = 17
IN2 = 18
IN3 = 22
IN4 = 23

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

def backward():
    GPIO.output(IN1, False)
    GPIO.output(IN2, True)
    GPIO.output(IN3, False)
    GPIO.output(IN4, True)

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
# pigpio GPS処理
# -------------------------------
RX_PIN = 27
BAUD = 9600
pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("pigpioデーモンに接続できません")

pi.bb_serial_read_open(RX_PIN, BAUD, 8)

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
                    lines = text.split("\n")
                    for line in lines:
                        if "$GNRMC" in line:
                            parts = line.strip().split(",")
                            if len(parts) > 6 and parts[2] == "A":
                                lat = convert_to_decimal(parts[3], parts[4])
                                lon = convert_to_decimal(parts[5], parts[6])
                                return lat, lon
            except Exception:
                continue
        time.sleep(0.1)
    raise TimeoutError("GPSデータの取得に失敗しました")

# -------------------------------
# 方位計算
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
# 色検出（赤）
# -------------------------------
def detect_color(camera):
    ret, frame = camera.read()
    if not ret:
        return None
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 120, 70])
    upper_red = np.array([10, 255, 255])
    mask = cv2.inRange(hsv, lower_red, upper_red)
    if np.sum(mask) > 5000:
        return "red"
    return None

# -------------------------------
# メイン処理
# -------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
init_motor()

camera = cv2.VideoCapture(0)

# BNO055初期化（IMU）
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)

# 目的地の座標（例：東京駅）
destination_lat = 35.681236
destination_lon = 139.767125

try:
    current_lat, current_lon = get_current_location()
    print(f"現在地：{current_lat}, {current_lon}")
    
    target_heading = calculate_heading(current_lat, current_lon, destination_lat, destination_lon)
    print(f"目的地への方位：{target_heading:.2f}°")

    heading = sensor.euler[0]
    if heading is None:
        heading = 0
    print(f"現在のIMU方位：{heading:.2f}°")

    diff = (target_heading - heading + 360) % 360
    if 10 < diff < 180:
        print("右旋回して調整")
        turn_right()
    elif diff >= 180:
        print("左旋回して調整")
        turn_left()
    else:
        print("方位OK")
        stop()

    time.sleep(2)

    color = detect_color(camera)
    if color == "red":
        print("赤色検出 → 右に避ける")
        turn_right()
        time.sleep(1)
    else:
        print("前進")
        forward()
        time.sleep(2)

    stop()
    print("停止")

finally:
    cleanup_motor()
    camera.release()
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    GPIO.cleanup()
    print("終了しました。")
