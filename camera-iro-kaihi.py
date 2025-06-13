import time
import cv2
import numpy as np
from datetime import datetime
from picamera import PiCamera
from motor import MotorDriver

# ==== 初期設定 ====
image_dir = "/home/pi/images"  # 撮影画像保存先
camera = PiCamera()
camera.resolution = (640, 480)

# モータードライバ初期化（ピン番号は必要に応じて修正）
motor = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,
    PWMB=19, BIN1=16, BIN2=26,
    STBY=21
)

# ==== 赤色検出関数 ====
def is_red_detected(image_path, threshold=1000):
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 赤色のHSV範囲
    lower1 = np.array([0, 70, 50])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([160, 70, 50])
    upper2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)

    red_area = cv2.countNonZero(mask)
    print(f"🔴 赤色面積: {red_area}")
    return red_area > threshold

# ==== メイン処理 ====
try:
    while True:
        # 撮影
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = f"{image_dir}/image_{now}.jpg"
        camera.capture(image_path)
        print(f"📸 撮影完了: {image_path}")
        
        # 赤色検出
        if is_red_detected(image_path):
            print("🔴 赤色を検出 → 回避行動開始")
            motor.motor_stop_free()
            time.sleep(0.5)
            motor.motor_right(60)
            time.sleep(1.0)
            motor.motor_forward(60)
            time.sleep(1.5)
            motor.motor_stop_free()
        else:
            print("🟢 赤なし → 前進")
            motor.motor_forward(60)
            time.sleep(1.5)
            motor.motor_stop_free()

        time.sleep(2)

except KeyboardInterrupt:
    print("❌ 中断されました")

finally:
    motor.cleanup()
    camera.close()
