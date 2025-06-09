import serial
import time

# IM920シリアル設定
im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

# 任意のGPS座標（例：東京駅）
target_lat = 35.681236
target_lon = 139.767125

# 送信文字列の組み立て（ローバーが受け取りやすい形式）
msg = "TXDU GPS:35.681236,139.767125\r\n"
im920.write(msg.encode())


# 送信
im920.write(msg.encode())
print(f"送信: {msg.strip()}")
