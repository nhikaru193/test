import math
import time
import pigpio
import RPi.GPIO as GPIO
from motor import MotorDriver  # ユーザーのMotorDriverクラスを使用
from BNO055 import BNO055
import smbus
import struct

# === モーター初期化 (変更なし) ===
driver = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,    # 左モーター
    PWMB=19, BIN1=16, BIN2=26,    # 右モーター
    STBY=21
)

# === 目標地点設定 (変更なし) ===
GOAL_LOCATION = [35.9180742, 139.9087919]  # 例：東京タワー

# === GPSピン設定 (変更なし) ===
RX_PIN = 17
BAUD = 9600

# === pigpio 初期化 (変更なし) ===
pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。sudo pigpiod を実行してください。")
    exit(1)

if pi.bb_serial_read_open(RX_PIN, BAUD, 8) != 0:
    print("ソフトUARTの初期化に失敗しました。")
    pi.stop()
    exit(1)

# === BNO055 初期化 (変更なし) ===
bno = BNO055()
#if not bno.begin():
    #print("BNO055の初期化に失敗しました。センサーの接続を確認してください。")
    #exit(1)
bno.begin()
time.sleep(1)
bno.setExternalCrystalUse(True)      #外部水晶振動子使用(クロック)
bno.setMode(BNO055.OPERATION_MODE_NDOF)  #NDOFモードに設定
time.sleep(1)
print("センサー類の初期化完了。ナビゲーションを開始します。")


# === 度分→10進変換関数 (変更なし) ===
def convert_to_decimal(coord, direction):
    if direction in ['N', 'S']:
        degrees = int(coord[:2])
        minutes = float(coord[2:])
    else:
        degrees = int(coord[:3])
        minutes = float(coord[3:])
    decimal = degrees + minutes / 60.0
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

while True:
    sys, gyro, accel, mag = bno.getCalibration()
    print(f"Calib → Sys:{sys}, Gyro:{gyro}, Acc:{accel}, Mag:{mag}", end='\r')
    if gyro == 3 and mag == 3:
        print("\n キャリブレーション完了！")
        break

# === GPS位置取得関数 (修正済み) ===
"""
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
                                return lat, lon
            except Exception as e:
                print("デコードエラー:", e)
        time.sleep(0.1)
"""
# === 2点間の方位角の計算 (可読性向上) ===
def get_bearing_to_goal(current, goal):
    if current is None or goal is None:
        return None
    lat1, lon1 = math.radians(current[0]), math.radians(current[1])
    lat2, lon2 = math.radians(goal[0]), math.radians(goal[1])
    delta_lon = lon2 - lon1
    y = math.sin(delta_lon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
    bearing_rad = math.atan2(y, x)
    return (math.degrees(bearing_rad) + 360) % 360

# === 2点間の距離の計算 (バグ修正済み) ===
def get_distance_to_goal(current, goal):
    if current is None or goal is None:
        return float('inf')
    lat1, lon1 = math.radians(current[0]), math.radians(current[1])
    lat2, lon2 = math.radians(goal[0]), math.radians(goal[1])
    radius = 6378137.0
    delta_lon = lon2 - lon1
    dist = radius * math.acos(math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(delta_lon))
    return dist

# === ナビゲーション制御 (ロジック改善済み) ===
def navigate_to_goal():
    try:
        while True:
            # 1. 状態把握
            current_location = 0, 0
            (count, data) = pi.bb_serial_read(RX_PIN)
            time.sleep(1.0)
            if count and data:
                try:
                    text = data.decode("ascii", errors="ignore")
                    if "$GNRMC" in text:
                        lines = text.split("\n")
                        for line in lines:
                            if "$GNRMC" in line:
                                parts = line.strip().split(",")
                                time.sleep(0.5)
                            if len(parts) > 6 and parts[2] == "A":
                                lat = convert_to_decimal(parts[3], parts[4])
                                lon = convert_to_decimal(parts[5], parts[6])
                                print("緯度と経度 (10進数):", [lat, lon])
                                current_location = lat, lon
                except Exception as e:
                    print("デコードエラー:", e)
            time.sleep(0.1)
            if not current_location:
                print("[WARN] GPS位置情報を取得できません。リトライします...")
                driver.motor_stop_brake()
                time.sleep(1)
                continue

            heading = bno.getVector(BNO055.VECTOR_EULER)[0]
            if heading is None:
                print("[WARN] BNO055から方位角を取得できません。リトライします...")
                driver.motor_stop_brake()
                time.sleep(1)
                continue

            # 2. 計算
            dist_to_goal = get_distance_to_goal(current_location, GOAL_LOCATION)
            bearing_to_goal = get_bearing_to_goal(current_location, GOAL_LOCATION)
            angle_error = (bearing_to_goal - heading + 360) % 360

            # 3. ゴール判定
            GOAL_THRESHOLD_M = 5.0
            if dist_to_goal <= GOAL_THRESHOLD_M:
                print(f"[GOAL] 目標地点に到達しました！ (距離: {dist_to_goal:.2f}m)")
                driver.motor_stop_brake()
                break

            print(f"[INFO] 距離:{dist_to_goal: >6.1f}m | 目標方位:{bearing_to_goal: >5.1f}° | 現在方位:{heading: >5.1f}° | 誤差:{angle_error: >5.1f}°")

            # 4. 方向調整フェーズ
            ANGLE_THRESHOLD_DEG = 10.0
            if angle_error > ANGLE_THRESHOLD_DEG and angle_error < (360 - ANGLE_THRESHOLD_DEG):
                turn_speed = 40 # 回転速度は固定
                # 誤差の大きさに応じて回転時間を変える
                turn_duration = 0.35 + (min(angle_error, 360 - angle_error) / 180.0) * 0.2

                if angle_error > 180:
                    print(f"[TURN] 左に回頭します ({turn_duration:.2f}秒)")
                    ### 元のモーター定義文を使用 ###
                    driver.changing_left(0, turn_speed)
                    driver.motor_stop_free()
                    time.sleep(turn_duration)
                else:
                    print(f"[TURN] 右に回頭します ({turn_duration:.2f}秒)")
                    ### 元のモーター定義文を使用 ###
                    driver.changing_right(0, turn_speed)
                    driver.motor_stop_free()
                    time.sleep(turn_duration)
                
                driver.motor_stop_brake()
                time.sleep(0.5)
                continue

            # 5. 前進フェーズ
            print("[MOVE] 方向OK。1秒間前進します。")
            move_speed = 90
            ### 元のモーター定義文を使用 ###
            driver.changing_forward(0, move_speed)
            time.sleep(1.0)
            driver.changing_forward(move_speed, 0)
            driver.motor_stop_free() # 元のコードに合わせてブレーキではなくフリーに
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n[STOP] 手動で停止されました。")
    except Exception as e:
        print(f"\n[FATAL] 予期せぬエラーが発生しました: {e}")
    finally:
        print("クリーンアップ処理を実行します。")
        ### 元のモーター定義文を使用 ###
        driver.cleanup()
        pi.bb_serial_read_close(RX_PIN)
        pi.stop()
        GPIO.cleanup()
        print("プログラムを終了しました。")

# === プログラム実行 ===
if __name__ == "__main__":
    navigate_to_goal()
