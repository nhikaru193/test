import math
import time
import pigpio
import RPi.GPIO as GPIO
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
            if math.fabs(angle_error) > 5:
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

            # 距離によって前進
            if dist > 100:
                move_duration = 5
            elif dist > 5:
                move_duration = 1.5
            else:
                print("[GOAL] 目標地点に到達しました！")
                driver.motor_stop_brake()
                break

            print(f"[MOVE] {move_duration:.1f}秒前進")
            driver.changing_forward(0, 90)
            time.sleep(move_duration)
            driver.motor_stop_free()

    except KeyboardInterrupt:
        print("[STOP] 手動停止されました")
    finally:
        driver.cleanup()
        pi.bb_serial_read_close(RX_PIN)
        pi.stop()

# === 実行 ===
if __name__ == "__main__":
    navigate_to_goal()
