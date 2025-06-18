import serial
import struct
import time

# テスト用の座標（例）
latitude = 35.123456
longitude = 139.654321

# 固定小数点化（100万倍）
lat_fixed = int(latitude * 1_000_000)     # 35123456
lon_fixed = int(longitude * 1_000_000)    # 139654321

# 9バイトのバイナリデータをパック（ヘッダ + 緯度 + 経度）
payload = struct.pack('>Bii', 0x01, lat_fixed, lon_fixed)

# バイナリを16進文字列に変換（例：b'\x01\x02' → '0102'）
hex_string = payload.hex().upper()

# TXDUコマンドを作成（宛先0003）
txdu_command = f'TXDU 0003,{hex_string}\r'

# シリアルポート初期化
ser = serial.Serial('/dev/serial0', 19200, timeout=1)
time.sleep(1)

# TXDUで送信
ser.write(txdu_command.encode('ascii'))
print("送信コマンド:", txdu_command.strip())

# 後始末
ser.close()
