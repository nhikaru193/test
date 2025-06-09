import math
import time
from motor_driver import MotorDriver  # 自作クラスファイル名がmotor_driver.pyであると仮定

# === 目標地点設定（[緯度, 経度]）===
GOAL_LOCATION = [35.6586, 139.7454]  # 例：東京タワー

# === GPSデータ取得（仮の実装）===
def get_current_gps_location():
    # L76Xから現在の緯度経度を取得する処理をここに書く
    return [35.6600, 139.7400]  # 仮データ（実装時に置き換えてください）

# === 方位角・距離の関数 ===
def direction(last_lng, location):
    x1 = math.radians(last_lng[0])
    y1 = math.radians(last_lng[1])
    x2 = math.radians(location[0])
    y2 = math.radians(location[1])
    delta_y = y2 - y1
    phi = math.atan2(math.sin(delta_y), math.cos(x1) * math.tan(x2) - math.sin(x1) * math.cos(delta_y))
    angle = (math.degrees(phi) + 360) % 360
    return angle

def distance(current_location, destination_location):
    x1 = math.radians(current_location[0])
    y1 = math.radians(current_location[1])
    x2 = math.radians(destination_location[0])
    y2 = math.radians(destination_location[1])
    R = 6378137.0
    d = R * math.acos(math.sin(y1) * math.sin(y2) + math.cos(y1) * math.cos(y2) * math.cos(x2 - x1))
    return d

# === モーター制御インスタンス作成 ===
motor = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,
    PWMB=19, BIN1=16, BIN2=26,
    STBY=21
)

# === メイン制御ループ ===
def navigate_to_goal():
    try:
        while True:
            current_location = get_current_gps_location()
            dist = distance(current_location, GOAL_LOCATION)
            angle_to_goal = direction(current_location, GOAL_LOCATION)
            current_heading = 0.0  # 北向きと仮定。実際は電子コンパスなどで取得推奨

            angle_error = (angle_to_goal - current_heading + 360) % 360
            print(f"[INFO] 距離: {dist:.2f} m, 目標角: {angle_to_goal:.2f}°, 誤差: {angle_error:.2f}°")

            # 方位誤差が2°以内に収まるまで右回転
            while abs(angle_error) > 2.0:
                print("[TURNING] 誤差が大きいため右回頭中...")
                motor.motor_right(speed=25)
                time.sleep(1)
                motor.motor_stop_free()
                current_location = get_current_gps_location()
                angle_to_goal = direction(current_location, GOAL_LOCATION)
                angle_error = (angle_to_goal - current_heading + 360) % 360

            # 距離によって前進時間を決定
            if dist > 100:
                forward_duration = 300
            else:
                forward_duration = 20

            print(f"[MOVING] {forward_duration}秒前進します")
            motor.motor_level2(speed=40)
            time.sleep(forward_duration)
            motor.motor_stop_free()

            # 再測定
            current_location = get_current_gps_location()
            dist = distance(current_location, GOAL_LOCATION)

            # 終了条件
            if dist <= 5.0:
                print("[GOAL] 目標地点に到達しました！")
                motor.motor_stop_brake()
                break

            print("[LOOP] 次のループへ移行...\n")

    except KeyboardInterrupt:
        print("[INTERRUPT] 停止します")
    finally:
        motor.cleanup()

# === 実行 ===
navigate_to_goal()
