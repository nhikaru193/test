import serial
import struct
import time

# 座標
latitude = 35.123456
longitude = 139.654321

# 固定小数点（百万倍して整数化）
lat_fixed = int(latitude * 1_000_000)     # 35123456
lon_fixed = int(longitude * 1_000_000)    # 139654321

# バイナリ化（1バイト:ヘッダ + 4バイト:緯度 + 4バイト:経度）
data = struct.pack('>Bii', 0x03, lat_fixed, lon_fixed)
# '>Bii' = ビッグエンディアン: 1バイト + 4バイト + 4バイト

# シリアルポート送信
ser = serial.Serial('/dev/serial0', 19200, timeout=1)
time.sleep(2)
ser.write(data)

print("送信バイナリ:", data.hex())
