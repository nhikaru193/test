from picamera2 import Picamera2
import time

# カメラ初期化
picam2 = Picamera2()

# 撮影設定（解像度：640x480など）
config = picam2.create_still_configuration(main={"size": (640, 480)})
picam2.configure(config)

# カメラスタート
picam2.start()
time.sleep(2)  # カメラの準備が整うまで少し待つ

# 保存先パス
image_path = "/home/mark1/picture/captured_image.jpg"

# 撮影して保存
picam2.capture_file(image_path)

# 終了
picam2.close()

print("画像を保存しました:", image_path)
