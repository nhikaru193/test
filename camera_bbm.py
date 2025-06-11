import cv2
import numpy as np
import time
from picamera2 import Picamera2

# カメラ初期化
picam2 = Picamera2()

# 撮影設定（解像度：640x480など）
config = picam2.create_still_configuration(main={"size": (640, 480)})
picam2.configure(config)

# カメラスタート
picam2.start()
time.sleep(2)  # カメラの準備が整うまで少し待つ

# 保存先パス
image_path = "/home/mark1/Pictures/captured_image.jpg"

# 撮影して保存
picam2.capture_file(image_path)

# 画像取得
frame = picam2.capture_array()

# BGR → HSV に変換
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# 赤色の範囲指定
lower_red1 = np.array([0, 30, 30])
upper_red1 = np.array([25, 255, 255])
lower_red2 = np.array([145, 30, 30])
upper_red2 = np.array([179, 255, 255])

# 赤マスク作成
mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
mask = cv2.bitwise_or(mask1, mask2)

# 面積計算
red_area = np.count_nonzero(mask)
total_area = frame.shape[0] * frame.shape[1]
percentage = (red_area / total_area) * 100

hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
center_pixel = hsv[hsv.shape[0]//2, hsv.shape[1]//2]
print("中心のHSV値:", center_pixel)

# 判定出力
print(f"🔴 赤割合: {percentage:.2f}% → ", end="")

# 終了
picam2.close()

print("画像を保存しました:", image_path)
