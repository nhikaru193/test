import math
import time
import pigpio
import RPi.GPIO as GPIO
from motor import MotorDriver 
from BNO055 import BNO055

# インスタンス生成：GPIOピン番号を正しく指定
driver = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,   # 左モーター用（モータA）
    PWMB=19, BIN1=16, BIN2=26,   # 右モーター用（モータB）
    STBY=21                      # STBYピン
)

# === 目標地点設定（[緯度, 経度]）===
GOAL_LOCATION = [35.6586, 139.7454]  # 例：東京タワー

# === GPSデータ取得（仮の実装）===
TX_PIN = 17
RX_PIN = 27
BAUD = 9600

pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

err = pi.bb_serial_read_open(RX_PIN, BAUD, 8)
if err != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}, {BAUD}bps")
    pi.stop()
    exit(1)

print(f"▶ ソフトUART RX を開始：GPIO={RX_PIN}, {BAUD}bps")

def convert_to_decimal(coord, direction):
    # 度分（ddmm.mmmm）形式を10進数に変換
    degrees = int(coord[:2]) if direction in ['N', 'S'] else int(coord[:3])
    minutes = float(coord[2:]) if direction in ['N', 'S'] else float(coord[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

try:
    while True:
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
                                print("緯度と経度 (10進数):", [lat, lon])
                                global last_lng = [lat, lon]
            except Exception as e:
                print("デコードエラー:", e)
        time.sleep(0.1)


# === 方位角・距離の関数 ===
last_lng = [lat, lon]
def direction(last_lng, GOAL_LOCATION):   #last_lng, locationはいずれも行列形式[latitude, longitude]　last_lngは現在地点, locationはゴール目標地点
    x1 = math.radians(last_lng[0])   #現在地点　緯度
    y1 = math.radians(last_lng[1])   #現在地点　経度
    x2 = math.radians(GOAL_LOCATION[0])   #目標地点　緯度
    y2 = math.radians(GOAL_LOCATION[1])   #目標地点　経度

    delta_y = y2 - y1
    #print("delta_y", delta_y)

    phi = math.atan2(math.sin(delta_y), math.cos(x1) * math.tan(x2) - math.sin(x1) * math.cos(delta_y))
    phi = math.degrees(phi)
    angle = (phi + 360) % 360
    #print("phi =", phi)
    return abs(angle) + (1 / 7200.0) #単位は°

# 2地点間の距離を計算
def distance(current_location, destination_location):
    x1 = math.radians(current_location[0])
    y1 = math.radians(current_location[1])
    x2 = math.radians(destination_location[0])
    y2 = math.radians(destination_location[1])

    radius = 6378137.0

    dist = radius * math.acos(math.sin(y1) * math.sin(y2) + math.cos(y1) * math.cos(y2) * math.cos(x2 - x1))

    return dist #単位はメートル

# === メイン制御ループ ===
def navigate_to_goal():
    try:
        while True:
            current_location = get_current_gps_location()
            dist = distance(current_location, GOAL_LOCATION)
            angle_to_goal = direction(current_location, GOAL_LOCATION)
            current_heading = 0.0  # 北向きと仮定。9軸でやりたい。

            angle_error = (angle_to_goal - current_heading + 360) % 360
            print(f"[INFO] 距離: {dist:.2f} m, 目標角: {angle_to_goal:.2f}°, 誤差: {angle_error:.2f}°")

            # 方位誤差が2°以内に収まるまで右回転
            while abs(angle_error) > 2.0:
                print("[TURNING] 誤差が大きいため右回頭中...")
                driver.changing_right(0, 25)
                time.sleep(1)
                driver.motor_stop_free()
                current_location = get_current_gps_location()
                angle_to_goal = direction(current_location, GOAL_LOCATION)
                angle_error = (angle_to_goal - current_heading + 360) % 360

            # 距離によって前進時間を決定
            if dist > 100:
                forward_duration = 300
            else:
                forward_duration = 20

                print(f"[MOVING] {forward_duration}秒前進します")

                driver.changing_forward(25, 80)
                time.sleep(forward_duration)
                driver.motor_stop_free()

            # 再測
            current_location = get_current_gps_location()
            dist = distance(current_location, GOAL_LOCATION)

            # 終了条件
            if dist <= 5.0:
                print("[GOAL] 目標地点に到達しました！")
                driver.motor_stop_brake()
                break

            print("[LOOP] 次のループへ移行...\n")

    except KeyboardInterrupt:
        print("[INTERRUPT] 停止します")
    finally:
        driver.cleanup()

# === 実行 ===
navigate_to_goal()
