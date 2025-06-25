import cv2
import numpy as np
import time
# picamera2ライブラリはラズベリーパイでのみ使用可能です
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("Info: picamera2 library not found. Running in image file mode.")

# --- 設定項目 ---
# 処理する画像ファイルへのパス (テスト用)
# ラズベリーパイでカメラを使う場合は、このファイルは使用されません。
TEST_IMAGE_PATH = 'image_e6ae9b.jpg' 

# 処理結果を保存するファイルへのパス
OUTPUT_IMAGE_PATH = "/home/mark1/Pictures/red_contour_final.jpg"

# 検出する色の範囲をHSVで指定します (赤色)
# 範囲1 (色相が0に近い赤)
LOWER_RED_1 = np.array([0, 100, 80])
UPPER_RED_1 = np.array([10, 255, 255])
# 範囲2 (色相が180に近い赤)
LOWER_RED_2 = np.array([160, 100, 80])
UPPER_RED_2 = np.array([179, 255, 255])

# ノイズとみなして無視する輪郭の最小面積
MIN_CONTOUR_AREA = 200

# 描画する輪郭の色 (BGR形式) と線の太さ
CONTOUR_COLOR_BGR = (127, 255, 0) # 黄緑色
CONTOUR_THICKNESS = 3
# -----------------


def main():
    """
    メインの処理を実行する関数
    """
    
    frame = None
    
    # picamera2が利用可能（ラズベリーパイ上）な場合
    if PICAMERA2_AVAILABLE:
        print("Starting camera...")
        picam2 = Picamera2()
        # 撮影設定（解像度など）を構成します
        config = picam2.create_still_configuration(main={"size": (640, 480)})
        picam2.configure(config)
        picam2.start()
        time.sleep(2)  # カメラの準備が整うまで待ちます

        # RGB形式で画像を取得し、OpenCVで扱えるBGR形式に変換します
        rgb_frame = picam2.capture_array()
        frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        
        # カメラを停止します
        picam2.close()
        print("Camera capture successful.")

    # picamera2が利用できない場合（PCでのテストなど）
    else:
        print(f"Reading image file: {TEST_IMAGE_PATH}")
        frame = cv2.imread(TEST_IMAGE_PATH)
        if frame is None:
            print(f"Error: Could not read the image file at {TEST_IMAGE_PATH}")
            return

    # --- 色検出と輪郭描画の処理 ---
    
    # 1. BGRからHSV色空間に変換します
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 2. 指定した赤色の範囲に基づいてマスクを作成します
    mask1 = cv2.inRange(hsv, LOWER_RED_1, UPPER_RED_1)
    mask2 = cv2.inRange(hsv, LOWER_RED_2, UPPER_RED_2)
    # 2つのマスクを結合して、赤色全体のマスクを取得します
    mask = cv2.bitwise_or(mask1, mask2)

    # 3. マスクから輪郭を検出します
    # RETR_EXTERNAL: 最も外側の輪郭のみを検出します
    # CHAIN_APPROX_SIMPLE: 輪郭の点を圧縮してメモリを節約します
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Found {len(contours)} initial contours.")

    # 4. 検出された輪郭を描画します
    for i, cnt in enumerate(contours):
        # 輪郭の面積を計算します
        area = cv2.contourArea(cnt)
        
        # 小さすぎる輪郭（ノイズ）は無視します
        if area > MIN_CONTOUR_AREA:
            print(f"  - Contour {i} (Area: {area:.0f}) is large enough. Drawing...")
            # 元の画像に輪郭線を描画します
            cv2.drawContours(
                image=frame, 
                contours=[cnt], 
                contourIdx=-1,  # -1は全ての輪郭を描画することを意味します
                color=CONTOUR_COLOR_BGR, 
                thickness=CONTOUR_THICKNESS
            )

    # 5. 結果を計算して表示します
    red_area = np.count_nonzero(mask)
    total_area = frame.shape[0] * frame.shape[1]
    percentage = (red_area / total_area) * 100
    print("-" * 20)
    print(f"🔴 Total Red Area Percentage: {percentage:.2f}%")
    print("-" * 20)

    # 6. 処理後の画像を保存します
    try:
        cv2.imwrite(OUTPUT_IMAGE_PATH, frame)
        print(f"Successfully saved the result to: {OUTPUT_IMAGE_PATH}")
    except Exception as e:
        print(f"Error: Could not save the image. {e}")
        # 保存に失敗した場合、デスクトップなど別の場所に保存を試みます
        try:
            fallback_path = "red_contour_result.jpg"
            cv2.imwrite(fallback_path, frame)
            print(f"Successfully saved to fallback path: {fallback_path}")
        except Exception as e_fallback:
             print(f"Error: Could not save to fallback path either. {e_fallback}")


if __name__ == '__main__':
    main()
