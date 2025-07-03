from picamera2 import Picamera2
from time import sleep
import cv2
import numpy as np

# --- 設定 ---
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
MIN_BLACK_AREA = 3000 # 検出対象とする黒領域の最小面積
GRID_COLS = 3 # 画面の分割数

def classify_shape(contour):
    """
    輪郭から頂点数と凸性(Solidity)を用いて図形を判別する
    """
    shape_name = "不明"
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    vertices = len(approx)

    # 面積が小さすぎるものはノイズとして無視
    if cv2.contourArea(contour) < 100:
        return "不明", None
    
    # 凸性を計算
    hull = cv2.convexHull(contour)
    solidity = 0
    if cv2.contourArea(hull) > 0:
        solidity = float(cv2.contourArea(contour)) / cv2.contourArea(hull)

    # 頂点数と凸性で判別
    if vertices == 3:
        shape_name = "三角形"
    elif vertices == 4:
        # 頂点数が4で、凸性が高い(凹みが少ない)ものは四角形
        if solidity > 0.95:
            shape_name = "長方形"
        else:
            # 凸性が低い場合はT字などの可能性
            shape_name = "T字"
    elif 5 <= vertices <= 8:
        # 頂点数が5-8で凸性が低いものはT字の可能性が高い
        if solidity < 0.9:
            shape_name = "T字"
    elif 9 <= vertices <= 14:
        # 頂点数が多く、凸性が低いものは十字の可能性
        if solidity < 0.75:
            shape_name = "十字"
    
    return shape_name, approx


def main():
    # 1. カメラの準備と撮影
    camera = Picamera2()
    config = camera.create_still_configuration(main={"size": (IMAGE_WIDTH, IMAGE_HEIGHT)})
    camera.configure(config)
    camera.start()
    sleep(2)
    
    # 直接画像データを取得
    img = camera.capture_array()
    camera.close()
    print("画像をカメラから直接取得しました。")

    if img is None:
        print("画像が取得できませんでした。")
        return

    # 2. 黒い領域を特定
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # 黒色のHSV範囲を調整 (より広い範囲の黒を捉える)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 50])
    black_mask = cv2.inRange(hsv, lower_black, upper_black)
    
    kernel = np.ones((5,5), np.uint8)
    black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, kernel)
    
    black_contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_black_regions = [c for c in black_contours if cv2.contourArea(c) >= MIN_BLACK_AREA]

    # 3. 図形検出と3分割カウント
    height, width, _ = img.shape
    block_w = width // GRID_COLS
    block_names = {i: name for i, name in enumerate(["左", "中央", "右"])}
    blocks_shapes = {i: [] for i in range(GRID_COLS)}

    for region_contour in valid_black_regions:
        x, y, w, h = cv2.boundingRect(region_contour)
        
        # 黒領域内の画像(ROI)を切り出す
        roi_img = img[y:y+h, x:x+w]
        
        # ROI内で図形を探す
        gray_roi = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        # 閾値処理で白い図形を抽出
        _, binary_roi = cv2.threshold(gray_roi, 100, 255, cv2.THRESH_BINARY)
        
        contours_in_roi, _ = cv2.findContours(binary_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours_in_roi:
            # 新しい判別関数を使用
            shape_name, approx = classify_shape(cnt)
            
            if shape_name == "不明" or approx is None:
                continue

            # 図形の重心を計算 (座標系を全体座標に戻す)
            M = cv2.moments(cnt)
            if M["m00"] == 0: continue
            # ROI内の座標
            cx_roi = int(M["m10"] / M["m00"])
            # 全体画像でのX座標
            global_cx = x + cx_roi

            # 所属ブロックを判定
            block_idx = min(global_cx // block_w, GRID_COLS - 1)
            blocks_shapes[block_idx].append(shape_name)

            # 描画処理
            # 輪郭の座標を全体座標に変換
            approx_global = approx + (x, y)
            cv2.drawContours(img, [approx_global], -1, (0, 255, 0), 2)
            
            bx, by, _, _ = cv2.boundingRect(approx_global)
            cv2.putText(img, shape_name, (bx, by - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # 黒領域の外枠を描画
        cv2.drawContours(img, [region_contour], -1, (255, 0, 0), 3)

    # 4. 結果の集計と表示
    # 区画線描画
    for i in range(1, GRID_COLS):
        cv2.line(img, (i * block_w, 0), (i * block_w, height), (0, 0, 255), 2)

    # ターミナルと画像に結果を出力
    print("\n--- 検出結果 ---")
    for i in range(GRID_COLS):
        counts = {s: blocks_shapes[i].count(s) for s in set(blocks_shapes[i])}
        text = ", ".join([f"{k}: {v}" for k, v in counts.items()]) if counts else "図形なし"
        
        print(f"{block_names[i]}: {text}")
        cv2.putText(img, f"{block_names[i]}:", (i * block_w + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(img, text, (i * block_w + 10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    # 5. 画像表示
    cv2.imshow("Detected Shapes", img)
    # cv2.imshow("Black Mask", black_mask) # デバッグ用にマスクを表示
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
