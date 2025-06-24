import cv2
import numpy as np
import time
from picamera2 import Picamera2

# カメラを初期化
picam2 = Picamera2()

# 撮影設定構成し
config = picam2.create_still_configuration(main={"size": (640, 480)})
picam2.configure(config)

# カメラ起動
picam2.start()
time.sleep(2) 

# 画像をNumPy配列として取得 (フォーマットRGB)
rgb_frame = picam2.capture_array()

# OpenCVで処理するために、RGBからBGRに色空間変換
frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

# BGRからHSVに変換
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# 赤色の範囲を指定
lower_red1 = np.array([0, 100, 80])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([160, 100, 80])
upper_red2 = np.array([179, 255, 255])

# 指定した範囲に基づいてマスク作成
mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
mask = cv2.bitwise_or(mask1, mask2)

# マスクから輪郭を検出
contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# 検出された輪郭をループ処理　　
for cnt in contours:
    # 輪郭の面積を計算し、ノイズは無視
    if cv2.contourArea(cnt) > 100:  # 面積が100ピクセルより大きい輪郭のみを対象
        # 輪郭を囲む長方形の座標を取得
        x, y, w, h = cv2.boundingRect(cnt)
        
        # 元の画像（BGR）に黄緑色の長方形を描画
        # cv2.rectangle(画像, 左上の座標, 右下の座標, 色(BGR), 線の太さ)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (127, 255, 0), 2)

# 赤色と判定された領域の面積を計算
red_area = np.count_nonzero(mask)
total_area = frame.shape[0] * frame.shape[1]
percentage = (red_area / total_area) * 100

# 画像中央のピクセルのHSV値を測定
center_pixel_hsv = hsv[frame.shape[0] // 2, frame.shape[1] // 2]
print(f"中心のHSV値: {center_pixel_hsv}")

# 判定結果を出力
print(f"🔴 赤色の割合: {percentage:.2f}%")

# 枠を描画した画像を保存するためのパス
output_image_path = "/home/mark1/Pictures/captured_image_with_box.jpg"

# 処理後の画像をファイルに保存
cv2.imwrite(output_image_path, frame)

# カメラを停止
picam2.close()

print(f"枠線付きの画像を保存しました: {output_image_path}")
