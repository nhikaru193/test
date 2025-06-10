import time
import RPi.GPIO as GPIO
import serial
import pynmea2
import cv2
import numpy as np
import board
import busio
import adafruit_bno055

# ===============================
# モーター制御の定義
# ===============================

# GPIOピンの定義（モーターA, B）
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

# ===============================
# GPS処理
# ===============================

def get_current_location():
    # シリアルポートとボーレートは環境に合わせて変更
    ser = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=1)
    while True:
        line = ser.readline().decode("utf-8", errors="ignore")
        if line.startswith('$GPGGA'):
            msg = pynmea2.parse(line)
            lat = msg.latitude
            lon = msg.longitude
            if lat and lon:
                return lat, lon

# ===============================
# 方位計算
# ===============================

def calculate_heading(current_lat, current_lon, dest_lat, dest_lon):
    import math
    delta_lon = math.radians(dest_lon - current_lon)
    y = math.sin(delta_lon) * math.cos(math.radians(dest_lat))
    x = math.cos(math.radians(current_lat)) * math.sin(math.radians(dest_lat)) - \
        math.sin(math.radians(current_lat)) * math.cos(math.radians(dest_lat)) * math.cos(delta_lon)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

# ===============================
# 色検出
# ===============================

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

# ===============================
# メイン処理
# ===============================

# GPIO初期化
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
init_motor()

# カメラ初期化
camera = cv2.VideoCapture(0)

# IMU初期化
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)

# 目的地
destination_lat = 35.681236
destination_lon = 139.767125

try:
    current_lat, current_lon = get_current_location()
    target_heading = calculate_heading(current_lat, current_lon, destination_lat, destination_lon)

    heading = sensor.euler[0]  # heading (yaw)
    if heading is None:
        heading = 0  # センサ未応答時は仮値

    diff = (target_heading - heading + 360) % 360

    if 10 < diff < 180:
        turn_right()
    elif diff >= 180:
        turn_left()
    else:
        stop()

    time.sleep(2)

    color = detect_color(camera)
    if color == "red":
        turn_right()
        time.sleep(1)
    else:
        forward()
        time.sleep(2)

    stop()

    # キャリブレーション（簡易的）
    print("キャリブレーション完了")

finally:
    cleanup_motor()
    camera.release()
    GPIO.cleanup()
