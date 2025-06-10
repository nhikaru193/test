from picamera2 import Picamera2
import time
from datetime import datetime

# カメラ初期化と設定
picam2 = Picamera2()
:contentReference[oaicite:1]{index=1}
:contentReference[oaicite:2]{index=2}

def take_photo_with_timestamp():
    :contentReference[oaicite:3]{index=3}
    :contentReference[oaicite:4]{index=4}
    :contentReference[oaicite:5]{index=5}

    # プレビュー・撮影・停止
    picam2.start()
    time.sleep(2)  # カメラウォームアップ
    picam2.capture_file(filename)
    picam2.stop()

    print(f"Captured {filename}")

:contentReference[oaicite:6]{index=6}
    take_photo_with_timestamp()
