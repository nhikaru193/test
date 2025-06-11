import serial
import pynmea2
import math
import time
import cv2
import numpy as np
import RPi.GPIO as GPIO
from picamera2 import Picamera2

# ==== GPS関係 ====
def get_gps_data():
    with serial.Serial('/dev/ttyS0', 9600, timeout=1) as ser:
        while True:
            line = ser.readline().decode('ascii', errors='replace')
            if line.startswith('$GPGGA'):
                try:
                    msg = pynmea2.parse(line)
                    lat = msg.latitude
                    lon = msg.longitude
                    return lat, lon
                except:
                    continue

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # m
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ==== モーター制御関係 ====
IN1, IN2, PWM, STBY = 17, 18, 12, 22

GPIO.setmode(GPIO.BCM)
GPIO.setup([IN1, IN2, PWM, STBY], GPIO.OUT)
pwm = GPIO.PWM(PWM, 1000)
pwm.start(0)

def move_forward(speed=50):
    GPIO.output(STBY, GPIO.HIGH)
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def stop_motors():
    GPIO.output(STBY, GPIO.LOW)
    pwm.ChangeDutyCycle(0)

def turn_left():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    pwm.ChangeDutyCycle(40)
    time.sleep(0.3)
    stop_motors()

def turn_right():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(40)
    time.sleep(0.3)
    stop_motors()

# ==== 目的地に移動 ====
def move_to_goal(dest_lat, dest_lon, threshold=2.0):
    print("目的地へ移動中...")
    while True:
        lat, lon = get_gps_data()
        distance = haversine(lat, lon, dest_lat, dest_lon)
        print(f"現在地: 緯度={lat:.6f}, 経度={lon:.6f} / 残り距離: {distance:.2f}m")
        if distance <= threshold:
            print("目的地に到達しました。")
            stop_motors()
            break
        else:
            move_forward(50)
            time.sleep(1)
    stop_motors()

# ==== 輪郭検出して向く ====
def start_contour_tracking():
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"size": (320, 240)}))
    picam2.start()
    print("カメラ起動：輪郭検出中...")

    try:
        while True:
            frame = picam2.capture_array()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                largest = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    center_x = frame.shape[1] // 2
                    tol = 20

                    if cx < center_x - tol:
                        turn_left()
                    elif cx > center_x + tol:
                        turn_right()
                    else:
                        move_forward(60)
                        time.sleep(0.5)
                        stop_motors()
                else:
                    stop_motors()
            else:
                stop_motors()

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        stop_motors()
        GPIO.cleanup()
        cv2.destroyAllWindows()

# ==== メイン ====
if __name__ == "__main__":
    try:
        目的地_lat = 35.6812     # 例：東京駅
        目的地_lon = 139.7671
        move_to_goal(目的地_lat, 目的地_lon)
        start_contour_tracking()
    except KeyboardInterrupt:
        print("終了します")
        stop_motors()
        GPIO.cleanup()
