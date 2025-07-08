import cv2
import numpy as np
from picamera2 import Picamera2
import os
import time # ファイル名にタイムスタンプを使用するためにインポート

def save_image_for_debug(picam2_instance, path="/home/mark1/Pictures/akairo.jpg"):
    """
    指定されたパスに現在のカメラフレームを保存します。
    
    Args:
        picam2_instance: Picamera2のインスタンス。
        path (str): 画像を保存するフルパス (例: /home/mark1/Pictures/akairo.jpg)。
    """
    try:
        # パスのディレクトリが存在するか確認し、なければ作成
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"ディレクトリを作成しました: {directory}")

        # 画像をキャプチャ
        frame_to_save = picam2_instance.capture_array()
        
        # OpenCVはBGR形式を扱うため、必要であれば変換 (picamera2はデフォルトでBGRのはずですが念のため)
        # もしPicamera2がRGBでキャプチャする設定になっている場合は、BGRに変換が必要
        # 例: frame_to_save = cv2.cvtColor(frame_to_save, cv2.COLOR_RGB2BGR)

        # 画像を保存
        cv2.imwrite(path, frame_to_save)
        print(f"デバッグ用画像を保存しました: {path}")
    except Exception as e:
        print(f"デバッグ用画像の保存中にエラーが発生しました: {e}")

def main():
    picam2 = Picamera2()
    
    # プレビュー設定 (解像度を下げることでZero 2 Wの負荷を軽減)
    camera_config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(camera_config)
    picam2.start()

    # カメラ起動後、デバッグ用に画像を保存
    # 注意: ここで一度画像を保存するため、ループに入る前に実行します
    # 保存するファイル名をタイムスタンプ付きにしたい場合は、以下のパスを調整してください
    # 例: current_time_str = time.strftime("%Y%m%d_%H%M%S")
    #     debug_save_path = f"/home/mark1/Pictures/akairo_debug_{current_time_str}.jpg"
    # save_image_for_debug(picam2, path=debug_save_path)
    save_image_for_debug(picam2, path="/home/mark1/Pictures/akairo.jpg")


    print("カメラを起動しました。赤色を検知しています...")

    try:
        while True:
            frame = picam2.capture_array()
            
            height, width, _ = frame.shape
            total_pixels = height * width

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])

            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])

            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            
            mask = cv2.add(mask1, mask2)

            res = cv2.bitwise_and(frame, frame, mask=mask)

            red_pixels = cv2.countNonZero(mask)

            if total_pixels > 0:
                red_percentage = (red_pixels / total_pixels) * 100
                print(f"赤色の割合: {red_percentage:.2f}% (赤色ピクセル数: {red_pixels}, 総ピクセル数: {total_pixels})")
            else:
                print("総ピクセル数が0です。")

            cv2.imshow('Original Frame', frame)
            cv2.imshow('Red Mask', mask)
            cv2.imshow('Red Detected', res)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("処理を中断します。")
    finally:
        picam2.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
