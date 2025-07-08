import cv2
import numpy as np
from picamera2 import Picamera2
import os
import time

def save_and_process_single_image(picam2_instance, save_path="/home/mark1/Pictures/akairo.jpg"):
    """
    カメラから一度だけ画像をキャプチャし、指定されたパスに保存します。
    保存後、その画像に対して赤色検知処理を行い、結果を出力します。
    キャプチャした画像を反時計回りに90度回転させてから処理します。

    Args:
        picam2_instance: Picamera2のインスタンス。
        save_path (str): 画像を保存するフルパス。
    """
    try:
        # ディレクトリが存在するか確認し、なければ作成
        directory = os.path.dirname(save_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"ディレクトリを作成しました: {directory}")

        print(f"画像をキャプチャし、{save_path}に保存します...")
        
        # 画像をキャプチャ (Picamera2はデフォルトでRGB形式のNumPy配列を返す)
        frame_rgb = picam2_instance.capture_array()
        
        # RGBからBGRに変換 (OpenCVがBGRを期待するため)
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        # --- ここから回転処理を追加 ---
        # 時計回りに90度傾いているので、反時計回りに90度（または時計回りに270度）回転させる
        # cv2.ROTATE_90_COUNTERCLOCKWISE は反時計回りに90度回転
        # cv2.ROTATE_90_CLOCKWISE は時計回りに90度回転 (これは今回の場合不要)
        # cv2.ROTATE_180 は180度回転
        rotated_frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
        print("画像を反時計回りに90度回転させました。")
        # --- 回転処理ここまで ---

        # 回転した画像を保存
        cv2.imwrite(save_path, rotated_frame_bgr) # 回転後の画像を保存
        print(f"画像を保存しました: {save_path}")

        # --- 保存した画像 (回転後の画像) に対して赤色検知処理を行う ---
        print("保存された画像に対して赤色検知を開始します...")

        # 回転後のフレームの高さと幅を使用
        height, width, _ = rotated_frame_bgr.shape
        total_pixels = height * width

        # BGRからHSV色空間に変換 (回転後の画像を使用)
        hsv = cv2.cvtColor(rotated_frame_bgr, cv2.COLOR_BGR2HSV)

        # 赤色のHSV範囲を定義
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])

        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        # マスクを作成し結合
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.add(mask1, mask2)

        # 赤色領域のピクセル数をカウント
        red_pixels = cv2.countNonZero(mask)

        # 赤色ピクセルの割合を計算
        if total_pixels > 0:
            red_percentage = (red_pixels / total_pixels) * 100
            print(f"最終結果: 赤色の割合は {red_percentage:.2f}% です。")
        else:
            print("総ピクセル数が0のため、赤色の割合を計算できませんでした。")

        # 結果をウィンドウ表示（任意）
        # デバッグ用や視覚確認のため、表示も回転後の画像を使用
        res = cv2.bitwise_and(rotated_frame_bgr, rotated_frame_bgr, mask=mask)
        cv2.imshow('Captured Original (Rotated)', rotated_frame_bgr) # 回転後の画像を表示
        cv2.imshow('Red Mask', mask)
        cv2.imshow('Red Detected', res)
        cv2.waitKey(0) # 何かキーが押されるまでウィンドウを開き続ける
        cv2.destroyAllWindows() # ウィンドウを閉じる

    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")

def main():
    picam2 = Picamera2()
    
    # プレビュー設定
    camera_config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(camera_config)
    picam2.start() # カメラを起動

    try:
        # 一度だけ撮影・保存・処理を行う関数を呼び出す
        save_and_process_single_image(picam2, save_path="/home/mark1/Pictures/akairo.jpg")

    except KeyboardInterrupt:
        print("プログラムを中断します。")
    finally:
        picam2.stop() # カメラを停止
        print("カメラを停止しました。プログラムを終了します。")

if __name__ == "__main__":
    main()
