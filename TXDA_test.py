import serial
import struct
import time

# ノード宛先設定（送信前に一度だけ）
def set_node_address(ser, node_id):
    cmd = f'ASTN {node_id:04d}\r'
    ser.write(cmd.encode('ascii'))
    time.sleep(0.1)

# 座標データ送信
def send_gps_data(ser, latitude, longitude):
    lat_fixed = int(latitude * 1_000_000)
    lon_fixed = int(longitude * 1_000_000)
    data = struct.pack('>Bii', 0x03, lat_fixed, lon_fixed)
    ser.write(data)
    print("送信バイナリ:", data.hex())

# 実行部分
ser = serial.Serial('/dev/serial0', 19200, timeout=1)
time.sleep(2)

# 宛先設定：0003ノードへ
set_node_address(ser, 3)

# データ送信
send_gps_data(ser, 35.123456, 139.654321)
