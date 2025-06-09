import serial
import time

# 送信側のシリアル設定（仮想ポートや物理ポート）
im920 = serial.Serial('/dev/serial0', 19200, timeout=1)  # 例: /dev/serial0 や COM1

# 任意のGPS座標（例：東京駅）
target_lat = 35.681236
target_lon = 139.767125

# 送信文字列の組み立て（ローバーが受け取りやすい形式）
msg = f"TXDA GPS:{target_lat},{target_lon}\r\n"

# 送信
im920.write(msg.encode())  # IM920にデータを送信
print(f"送信: {msg.strip()}")

# 1秒待機（次の送信まで）
time.sleep(1)
