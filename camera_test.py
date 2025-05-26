import subprocess
from datetime import datetime

# 保存ファイル名を現在時刻で作成
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"/home/pi/Pictures/image_{timestamp}.jpg"

# libcamera-stillコマンドで撮影
subprocess.run([
    "libcamera-still",
    "-o", filename,
    "--width", "1280",
    "--height", "720",
    "--nopreview"
])

print(f"画像を保存しました: {filename}")
