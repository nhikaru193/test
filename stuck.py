import time
import math
from your_gps_module import get_gps_location  # L76X用GPS取得関数
from your_motor_control_module import backward, forward, rotate, stop_motors

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # m
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def stack_escape_sequence(pattern):
    if pattern == 0:
        backward(1.0)
        rotate(0.5)
        forward(1.0)
    else:
        forward(1.0)
        rotate(0.5)
        backward(1.0)

def wait_and_get_gps():
    # GPS更新のため少し待つ
    time.sleep(2)
    for _ in range(5):
        lat, lon = get_gps_location()
        if lat and lon:
            return lat, lon
        time.sleep(1)
    return None, None

def handle_stack(initial_lat, initial_lon, threshold=1.5):
    pattern = 0
    for attempt in range(5):
        print(f"スタック解除試行: {attempt + 1}")
        stack_escape_sequence(pattern)
        stop_motors()
        new_lat, new_lon = wait_and_get_gps()

        if not new_lat:
            print("GPS取得失敗")
            continue

        moved = calculate_distance(initial_lat, initial_lon, new_lat, new_lon)
        print(f"移動距離: {moved:.2f}m")

        if moved > threshold:
            print("スタック解除成功！")
            return True

        pattern = 1 - pattern  # パターン切替
    print("スタック解除失敗…")
    return False

def main_task():
    start_lat, start_lon = wait_and_get_gps()
    if not start_lat:
        print("初期GPS取得失敗")
        return

    # ここに通常の処理を書く
    forward(2.0)  # 例：前進処理
    stop_motors()

    end_lat, end_lon = wait_and_get_gps()
    if not end_lat:
        print("GPS取得失敗")
        return

    moved = calculate_distance(start_lat, start_lon, end_lat, end_lon)
    print(f"移動距離: {moved:.2f}m")

    if moved < 1.0:
        print("スタック判定！")
        handle_stack(start_lat, start_lon)
    else:
        print("正常移動")

if __name__ == "__main__":
    main_task()
