import time
import math
import board
import busio
import serial
import cv2
import numpy as np
from gpiozero import Motor
from picamera2 import Picamera2
import adafruit_bno055

# --- 初期設定 ---
GOAL_LAT = 35.123456
GOAL_LON = 139.123456
BEARING_TOLERANCE = 15
AVOID_LIMIT = 3
WAIT_DURATION = 5

# --- モーター設定 ---
left_motor = Motor(forward=17, backward=18)
right_motor = Motor(forward=22, backward=23)

def move_forward():
    left_motor.forward()
    right_motor.forward()

def stop():
    left_motor.stop()
    right_motor.stop()

def turn_left():
    left_motor.backward()
    right_motor.forward()

def turn_right():
    left_motor.forward()
    right_motor.backward()

# --- センサ初期化 ---
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)
gps = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'RGB888', "size": (320, 240)}))
camera.start()

# --- 赤色検出範囲（HSV） ---
LOWER_RED1 = np.array([0, 120, 70])
UPPER_RED1 = np.array([10, 255, 255])
LOWER_RED2 = np.array([170, 120, 70])
UPPER_RED2 = np.array([180, 255, 255])

# --- 関数定義 ---
def convert_to_decimal(coord, direction):
    if coord == '': return None
    deg = float(coord[:2])
    minutes = float(coord[2:])
    decimal = deg + minutes / 60
    return -decimal if direction in ['S', 'W'] else decimal

def get_gps_position():
    line = gps.readline().decode('ascii', errors='replace')
    if "$GNRMC" in line or "$GPRMC" in line:
        parts = line.split(',')
        if parts[2] == 'A':
            lat = convert_to_decimal(parts[3], parts[4])
            lon = convert_to_decimal(parts[5], parts[6])
            return lat, lon
    return None, None

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
    bearing = math.atan2(x, y)
    return (math.degrees(bearing) + 360) % 360

def detect_red_centroid(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    mask1 = cv2.inRange(hsv, LOWER_RED1, UPPER_RED1)
    mask2 = cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
    red_mask = cv2.bitwise_or(mask1, mask2)
    M = cv2.moments(red_mask)
    if M["m00"] > 5000:
        cx = int(M["m10"] / M["m00"])
        return cx
    return None

# --- メイン処理 ---
print("🚀 ミッション開始")
avoid_count = 0
color_detection_mode = False
goal_reached = False

try:
    # --- 目標方向へ向くフェーズ ---
    while not color_detection_mode:
        lat, lon = get_gps_position()
        heading = sensor.euler[0]
        if lat and lon and heading is not None:
            goal_bearing = calculate_bearing(lat, lon, GOAL_LAT, GOAL_LON)
            diff = abs(goal_bearing - heading)
            if diff > 180:
                diff = 360 - diff
            print(f"現在方位: {heading:.1f}°, 目的地方位: {goal_bearing:.1f}°, 差: {diff:.1f}°")
            if diff < BEARING_TOLERANCE:
                print("✅ 向き完了 → 色検知モードへ")
                color_detection_mode = True
            else:
                print("🔄 向き調整中...")
                move_forward()
                time.sleep(1)
                stop()
        time.sleep(0.5)

    # --- 色検知＆回避・最終GPS取得 ---
    while not goal_reached:
        frame = camera.capture_array()
        centroid = detect_red_centroid(frame)

        if centroid is None:
            print("🟢 パラシュートなし → 前進してGPS再取得")
            move_forward()
            time.sleep(2)
            stop()

            # --- GPS再取得 ---
            lat, lon = get_gps_position()
            if lat and lon:
                print(f"📍 再取得位置: 緯度={lat}, 経度={lon}")
            else:
                print("⚠️ GPS取得失敗")

            # --- キャリブレーション ---
            heading = sensor.euler[0]
            if heading is not None:
                print(f"🧭 キャリブレーション完了。最終方位: {heading:.2f}°")
            else:
                print("⚠️ 方位センサ読み取り失敗")

            print("✅ ミッション完了（回避 → GPS → 停止 → キャリブレーション）")
            goal_reached = True
            break

        else:
            print(f"🔴 パラシュート検知 → 回避実行中 ({avoid_count+1})")
            avoid_count += 1
            if avoid_count >= AVOID_LIMIT:
                print("⚠️ 被さり判定 → 停止して待機")
                stop()
                time.sleep(WAIT_DURATION)
                avoid_count = 0
                continue

            if centroid < 100:
                turn_right()
            elif centroid > 220:
                turn_left()
            else:
                stop()
            time.sleep(0.5)

except KeyboardInterrupt:
    print("⛔ 手動停止")
finally:
    stop()
    print("🛑 ローバー停止完了")
