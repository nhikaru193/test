import cv2
import numpy as np
import time
from picamera2 import Picamera2

# カメラを初期化します
picam2 = Picamera2()

# 撮影設定（解像度：640x480など）を構成します
config = picam2.create_still_configuration(main={"size": (640, 480)})
picam2.configure(config)

# カメラを起動します
picam2.start()
time.sleep(2)  # カメラの準備が整うまで2秒間待ちます

# 画像をNumPy配列として取得します (フォーマットはRGB)
rgb_frame = picam2.capture_array()

# OpenCVで処理するために、RGBからBGRに色空間を変換します
frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

# BGRからHSVに変換します
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# 赤色の範囲を指定します
# H(色相)の値が0-20と95-130の範囲を赤色として検出します
# 注意: 95-130の範囲は、一般的には青色系の色相です。もし意図と異なる場合は、[160, 30, 30]のように調整してください。
lower_red1 = np.array([0, 100, 80])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([160, 100, 80])
upper_red2 = np.array([179, 255, 255])

# 指定した範囲に基づいてマスクを作成します
mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
mask = cv2.bitwise_or(mask1, mask2)

# --- ここからが追加された処理です ---

# マスクから輪郭を検出します
contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# 検出された輪郭をループ処理します　　
for cnt in contours:
    # 輪郭の面積を計算し、小さすぎるもの（ノイズ）は無視します
    if cv2.contourArea(cnt) > 100:  # 面積が100ピクセルより大きい輪郭のみを対象
        # 輪郭を囲む長方形（バウンディングボックス）の座標を取得します
        x, y, w, h = cv2.boundingRect(cnt)
        
        # 元の画像（BGR）に黄緑色の長方形を描画します
        # cv2.rectangle(画像, 左上の座標, 右下の座標, 色(BGR), 線の太さ)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (127, 255, 0), 2)

# --- 追加処理はここまでです ---

# 赤色と判定された領域の面積を計算します
red_area = np.count_nonzero(mask)
total_area = frame.shape[0] * frame.shape[1]
percentage = (red_area / total_area) * 100

# 画像中央のピクセルのHSV値を測定します
center_pixel_hsv = hsv[frame.shape[0] // 2, frame.shape[1] // 2]
print(f"中心のHSV値: {center_pixel_hsv}")

# 判定結果を出力します
print(f"🔴 赤色の割合: {percentage:.2f}%")

# 枠を描画した画像を保存するためのパス
output_image_path = "/home/mark1/Pictures/captured_image_with_box.jpg"

# 処理後の画像をファイルに保存します
cv2.imwrite(output_image_path, frame)

# カメラを停止・解放します
picam2.close()

print(f"枠線付きの画像を保存しました: {output_image_path}")
