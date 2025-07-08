import cv2
import numpy as np
from picamera2 import Picamera2

def main():
    picam2 = Picamera2()
    
    # プレビュー設定 (解像度を下げることでZero 2 Wの負荷を軽減)
    # Zero 2 Wでは320x240などの低い解像度が推奨されます
    # 解像度を変更した場合は、total_pixelsの計算もそれに合わせる必要があります
    camera_config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(camera_config)
    picam2.start()

    print("カメラを起動しました。赤色を検知しています...")

    try:
        while True:
            frame = picam2.capture_array()
            
            # フレームの高さと幅を取得し、総ピクセル数を計算
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

            # 赤色ピクセルの割合を計算
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
