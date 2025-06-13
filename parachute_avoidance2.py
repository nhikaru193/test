import math
import time
import pigpio
import cv2
import numpy as np
import RPi.GPIO as GPIO
from picamera2 import Picamera2
from motor import MotorDriver 
from BNO055 import BNO055

# === モーター初期化 ===
driver = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,   # 左モーター
    PWMB=19, BIN1=16, BIN2=26,   # 右モーター
    STBY=21
)

# === 目標地点設定 ===
GOAL_LOCATION = [35.6586, 139.7454]  # 例：東京タワー

# === GPSピン設定 ===
TX_PIN = 17
RX_PIN = 27
BAUD = 9600

pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

if pi.bb_serial_read_open(RX_PIN, BAUD, 8) != 0:
    print("ソフトUARTの初期化に失敗")
    pi.stop()
    exit(1)

# === BNO055 初期化 ===
bno = BNO055()
if not bno.begin():
    print("BNO055の初期化に失敗しました")
    exit(1)

# === 度分→10進変換 ===
def convert_to_decimal(coord, direction):
    degrees = int(coord[:2]) if direction in ['N', 'S'] else int(coord[:3])
    minutes = float(coord[2:]) if direction in ['N', 'S'] else float(coord[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

# === GPS位置取得関数 ===
def get_current_gps_location():
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
                            return [lat, lon]
        except Exception as e:
            print("GPSデコードエラー:", e)
    return None

# === 方位角の計算 ===
def direction(goal_location):                    #direction(GOAL_LOCATION)
    current = get_current_gps_location()
    goal = goal_location
    x1 = math.radians(current[0]) #この辺怪し
    y1 = math.radians(current[1])#この辺怪し
    x2 = math.radians(goal_location[0]) #この辺怪し
    y2 = math.radians(goal_location[1])#この辺怪し

    delta_y = y2 - y1
    phi = math.atan2(math.sin(delta_y), math.cos(x1)*math.tan(x2) - math.sin(x1)*math.cos(delta_y))
    phi = math.degrees(phi)
    return (phi + 360) % 360

# === 距離の計算 ===
def distance(current, goal):
    x1 = math.radians(current[0]) #この辺怪し
    y1 = math.radians(current[1])#この辺怪し
    x2 = math.radians(goal_location[0]) #この辺怪し
    y2 = math.radians(goal_location[1])#この辺怪し

    radius = 6378137.0
    dist = radius * math.acos(math.sin(y1) * math.sin(y2) + math.cos(y1) * math.cos(y2) * math.cos(x2 - x1))

    return dist #単位はメートル

# === ナビゲーション制御 ===
def navigate_to_goal():
    try:
        while True:
            current_location = get_current_gps_location()
            if not current_location:
                print("[WARN] GPS位置取得に失敗。再試行します...")
                time.sleep(1)
                continue

            dist = distance(current_location, GOAL_LOCATION)
            angle_to_goal = direction(GOAL_LOCATION)

            heading = bno.getVector(BNO055.VECTOR_EULER)[0]  # yaw
            angle_error = (angle_to_goal + heading + 360) % 360

            print(f"[INFO] 距離: {dist:.2f}m | 目標角: {angle_to_goal:.2f}° | 現在角: {heading:.2f}° | 誤差: {angle_error:.2f}°")

            # 誤差に応じて方向調整
            if angle_error > 5:
                if angle_error > 180:
                    print("[TURN] 左回頭")
                    driver.changing_left(0, 25)
                    time.sleep(0.5)
                    driver.changing_left(25, 0)
                    time.sleep(0.5)
                else:
                    print("[TURN] 右回頭")
                    driver.changing_right(0, 25)
                    time.sleep(0.5)
                    driver.changing_right(25, 0)
                    time.sleep(0.5)
                    driver.motor_stop_brake()
                continue  # 再評価

# === Picamera2 初期化 ===
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

def detect_red_object():
    frame = picam2.capture_array()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 赤色のHSV範囲（2つに分かれる）
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    red_area = cv2.countNonZero(mask)
    return red_area > 500  # 赤色領域が一定以上なら検出とみなす

# === ナビゲーション制御の続き ===
            if dist < 2.0:
                print("[GOAL] 目的地に到達しました。")
                driver.motor_stop_brake()
                break

            if detect_red_object():
                print("[DETECT] 赤色物体検出！回避行動")
                driver.motor_quick_right(25)  # クイックライト旋回
                time.sleep(1.0)
                driver.motor_forward(30, 30)
                time.sleep(1.5)
            else:
                print("[MOVE] 前進中")
                driver.motor_forward(30, 30)
                time.sleep(1.5)
    except KeyboardInterrupt:
        print("中断されました")
        driver.motor_stop_brake()
    finally:
        picam2.stop()
        pi.bb_serial_read_close(RX_PIN)
        pi.stop()
        GPIO.cleanup()
