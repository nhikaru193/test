from picamera2 import Picamera2
from time import sleep
import cv2
import numpy as np

# 頂点数に応じて図形名を返す関数
def classify_by_vertex_count(contour):
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    vertices = len(approx)
    shape_name = "多角形"
    if vertices == 3:
        shape_name = "三角形"
    elif vertices == 4:
        shape_name = "長方形"
    elif vertices == 8:
        shape_name = "T字"
    elif vertices == 12:
        shape_name = "十字"
    elif vertices == 16:
        shape_name = "Eみたいなやつ"
    return shape_name, approx

# 撮影
camera = Picamera2()
config = camera.create_still_configuration(main={"size": (320, 240)})
camera.configure(config)
camera.start()
sleep(2)
image_path = '/home/mark1/Pictures/captured_image.jpg'
camera.capture_array()
camera.capture_file(image_path)
camera.close()
print("画像を保存しました:", image_path)

# 読み込みと前処理
img = cv2.imread(image_path)
if img is None:
    print("画像が読み込めませんでした。")
    exit()

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower_black = np.array([0, 0, 0])
upper_black = np.array([180, 50, 50])
black_mask = cv2.inRange(hsv, lower_black, upper_black)
kernel = np.ones((5,5), np.uint8)
black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, kernel)
black_mask_blur = cv2.GaussianBlur(black_mask, (5,5), 0)

# 黒領域の輪郭抽出
min_black_area = 5000
black_contours, _ = cv2.findContours(black_mask_blur, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
valid_black_regions = [c for c in black_contours if cv2.contourArea(c) >= min_black_area]

# 図形検出と3分割カウント
height, width = img.shape[:2]
grid_cols = 3
block_w = width // grid_cols
block_names = {0: "左", 1: "中央", 2: "右"}
blocks_shapes = {0: [], 1: [], 2: []}

for region_contour in valid_black_regions:
    mask_roi = np.zeros((height, width), dtype=np.uint8)
    cv2.drawContours(mask_roi, [region_contour], -1, 255, thickness=cv2.FILLED)
    x, y, w, h = cv2.boundingRect(region_contour)
    roi_mask = mask_roi[y:y+h, x:x+w]
    roi_img = img[y:y+h, x:x+w]
    gray_roi = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    masked_gray = cv2.bitwise_and(gray_roi, gray_roi, mask=roi_mask)
    _, binary_roi = cv2.threshold(masked_gray, 50, 255, cv2.THRESH_BINARY)
    contours_roi, _ = cv2.findContours(binary_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours_roi:
        shape_name, approx = classify_by_vertex_count(cnt)
        if len(approx) < 3:
            continue

        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        global_cx = x + cx

        block_idx = min(global_cx // block_w, grid_cols - 1)
        blocks_shapes[block_idx].append(shape_name)

        # 図形描画
        cv2.drawContours(roi_img, [approx], -1, (0, 255, 0), 2)
        bx, by, bw, bh = cv2.boundingRect(approx)
        cv2.putText(roi_img, shape_name, (bx, by - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

    # 黒領域の外枠描画
    cv2.drawContours(img, [region_contour], -1, (255, 0, 0), 3)

# 区画線描画
for i in range(1, grid_cols):
    cv2.line(img, (i * block_w, 0), (i * block_w, height), (255, 0, 0), 2)

# 各エリアの図形情報を画像に描画
for i in range(grid_cols):
    shapes_in_block = blocks_shapes[i]
    if not shapes_in_block:
        continue
    counts = {}
    for s in shapes_in_block:
        counts[s] = counts.get(s, 0) + 1
    text = ", ".join([f"{k}: {v}" for k, v in counts.items()])
    cv2.putText(img, f"{block_names[i]}: {text}", (i * block_w + 10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

# ターミナルに出力
for i in range(grid_cols):
    shapes_in_block = blocks_shapes[i]
    if not shapes_in_block:
        print(f"{block_names[i]}: 図形なし")
        continue
    counts = {}
    for s in shapes_in_block:
        counts[s] = counts.get(s, 0) + 1
    text = ", ".join([f"{k}: {v}" for k, v in counts.items()])
    print(f"{block_names[i]}: {text}")

# 黒領域マスク表示
mask_detected = np.zeros((height, width), dtype=np.uint8)
for region_contour in valid_black_regions:
    cv2.drawContours(mask_detected, [region_contour], -1, 255, thickness=cv2.FILLED)

cv2.imshow("Detected Black Regions Mask", mask_detected)
cv2.imshow("Detected Shapes by Name (3分割)", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
