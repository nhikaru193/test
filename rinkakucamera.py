from picamera2 import Picamera2
from time import sleep
import cv2
import numpy as np
import math

def calculate_circularity(contour):
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return 0
    return 4 * math.pi * area / (perimeter * perimeter)

def classify_shape(contour):
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    vertices = len(approx)
    area = cv2.contourArea(contour)
    if area < 100:
        return None, approx
    shape = "不明"
    if vertices == 3:
        shape = "三角形"
    elif vertices == 4:
        x, y, w, h = cv2.boundingRect(approx)
        ar = float(w) / h
        if 0.95 <= ar <= 1.05:
            shape = "正方形"
        else:
            shape = "長方形"
    elif vertices == 5:
        shape = "五角形"
    elif vertices == 6:
        shape = "六角形"
    else:
        circularity = calculate_circularity(contour)
        if circularity > 0.85:
            shape = "円形"
        else:
            shape = "多角形"
    return shape, approx

# ----- 撮影 -----
camera = Picamera2()
camera.resolution = (640, 480)
camera.start_preview()
sleep(2)
image_path = '/home/pi/captured_image.jpg'
camera.capture(image_path)
camera.close()
print("画像を保存しました:", image_path)

# ----- 検出 -----
img = cv2.imread(image_path)
if img is None:
    print("画像が読み込めませんでした。")
    exit()

# 以下、あなたの元コード（HSV変換、輪郭検出など）を貼り付けて使用
# 省略部分に、あなたの処理全体を入れてください
# 例：
# hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# （略）
# cv2.imshow("Detected Shapes", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

 
# HSVに変換
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
 
# 黒色の範囲を狭める
lower_black = np.array([0, 0, 0])
upper_black = np.array([180, 50, 50])
 
black_mask = cv2.inRange(hsv, lower_black, upper_black)
 
# モルフォロジー処理でノイズ除去
kernel = np.ones((5,5), np.uint8)
black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, kernel)
 
# ぼかしでノイズをさらに低減
black_mask_blur = cv2.GaussianBlur(black_mask, (5,5), 0)
 
# 輪郭検出
black_contours, _ = cv2.findContours(black_mask_blur, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
 
min_black_area = 10000  # 面積基準を上げる
 
rect_black_regions = []
for bc in black_contours:
    area = cv2.contourArea(bc)
    if area < min_black_area:
        continue
    epsilon = 0.01 * cv2.arcLength(bc, True)  # 近似度を調整
    approx = cv2.approxPolyDP(bc, epsilon, True)
    if len(approx) == 4 and cv2.isContourConvex(approx):
        x, y, w, h = cv2.boundingRect(approx)
        ar = w / h
        if 0.7 < ar < 1.3:  # ほぼ長方形 or 正方形
            rect_black_regions.append((x, y, w, h, approx))
 
 
# 黒領域の輪郭検出（多角形もOK）
min_black_area = 5000
black_contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
 
# 面積一定以上の黒領域だけ抽出
valid_black_regions = []
for bc in black_contours:
    area = cv2.contourArea(bc)
    if area < min_black_area:
        continue
    valid_black_regions.append(bc)
 
# 3分割の幅設定
grid_cols = 3
block_w = width // grid_cols
block_names = {0: "左", 1: "中央", 2: "右"}
blocks_shapes = {0: [], 1: [], 2: []}
 
for region_contour in valid_black_regions:
    # 黒領域のマスク作成（画像全体サイズ）
    mask_roi = np.zeros((height, width), dtype=np.uint8)
    cv2.drawContours(mask_roi, [region_contour], -1, 255, thickness=cv2.FILLED)
 
    # 黒領域の矩形でROI切り出し
    x, y, w, h = cv2.boundingRect(region_contour)
    roi_mask = mask_roi[y:y+h, x:x+w]
    roi_img = img[y:y+h, x:x+w]
 
    # ROIグレースケール化＋マスク適用
    gray_roi = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    masked_gray = cv2.bitwise_and(gray_roi, gray_roi, mask=roi_mask)
 
    # 二値化（適宜調整）
    _, binary_roi = cv2.threshold(masked_gray, 50, 255, cv2.THRESH_BINARY)
 
    # ROI内の輪郭検出
    contours_roi, _ = cv2.findContours(binary_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
 
    for cnt in contours_roi:
        shape, approx = classify_shape(cnt)
        if shape is None:
            continue
 
        # 重心計算
        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        # グローバル座標に変換
        global_cx = x + cx
 
        # 3分割ブロック判定
        block_idx = min(global_cx // block_w, grid_cols - 1)
        blocks_shapes[block_idx].append(shape)
 
        # 図形描画
        cv2.drawContours(roi_img, [approx], -1, (0, 255, 0), 2)
        bx, by, bw, bh = cv2.boundingRect(approx)
        cv2.putText(roi_img, shape, (bx, by - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
 
    # 元画像に黒領域の輪郭描画
    cv2.drawContours(img, [region_contour], -1, (255, 0, 0), 3)
 
# 以下、3分割ライン描画やテキスト表示、結果のプリントは今まで通り
 
# 横3分割のライン描画
for i in range(1, grid_cols):
    cv2.line(img, (i * block_w, 0), (i * block_w, height), (255, 0, 0), 2)
 
# 画像に各ブロックの図形情報を描画
for i in range(grid_cols):
    shapes_in_block = blocks_shapes[i]
    if not shapes_in_block:
        continue
    counts = {}
    for s in shapes_in_block:
        counts[s] = counts.get(s, 0) + 1
    text = ", ".join([f"{k}:{v}" for k, v in counts.items()])
    cv2.putText(img, f"{block_names[i]}: {text}", (i * block_w + 10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
 
# ターミナルに結果表示
for i in range(grid_cols):
    shapes_in_block = blocks_shapes[i]
    if not shapes_in_block:
        print(f"{block_names[i]}: 図形なし")
        continue
    counts = {}
    for s in shapes_in_block:
        counts[s] = counts.get(s, 0) + 1
    text = ", ".join([f"{k}:{v}" for k, v in counts.items()])
    print(f"{block_names[i]}: {text}")
 
mask_detected = np.zeros((height, width), dtype=np.uint8)
 
for region_contour in valid_black_regions:
    cv2.drawContours(mask_detected, [region_contour], -1, 255, thickness=cv2.FILLED)
 
# 表示
cv2.imshow("Detected Black Rectangles Mask", mask_detected)
cv2.imshow("Detected Shapes inside Black Rectangles (3分割)", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
