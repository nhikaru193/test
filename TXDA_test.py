import serial
import struct
import time

# テスト用の緯度・経度（例）
latitude = 35.123456
longitude = 139.654321

# 固定小数点に変換（百万倍）
lat_fixed = int(latitude * 1_000_000)     # => 35123456
lon_fixed = int(longitude * 1_000_000)    # => 139654321

# バイナリパケット作成（9バイト：ヘッダ1 + 緯度4 + 経度4）
# '>Bii' = ビッグエンディアン, 1バイト (unsigned), 4バイト (signed), 4バイト (signed)
packet = struct.pack('>Bii', 0x01, lat_fixed, lon_fixed)

# シリアルポートを開く
ser = serial.Serial('/dev/serial0', 19200, timeout=1)
time.sleep(1)

# 送信先ノードを指定（ASTNコマンド）※1回だけでOK
ser.write(b'ASTN 0003\r')
time.sleep(0.1)

# バイナリデータを送信
ser.write(packet)

print("送信データ（HEX）:", packet.hex())
print("送信完了")

# 終了処理
ser.close()
