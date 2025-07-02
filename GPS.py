import serial
import time
import pigpio
import math
import struct

def init_L76X():
    global TX_PIN, RX_PIN, BAUD
    TX_PIN = 27
    RX_PIN = 17
    BAUD = 9600
    pi = pigpio.pi()
    if not pi.connected:
        print("pigpio デーモンに接続できません。")
        exit(1)
    err = pi.bb_serial_read_open(RX_PIN, BAUD, 8)
    if err != 0:
        print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}, {BAUD}bps")

def convert_to_decimal(coord, direction):
    # 度分（ddmm.mmmm）形式を10進数に変換
    degrees = int(coord[:2]) if direction in ['N', 'S'] else int(coord[:3])
    minutes = float(coord[2:]) if direction in ['N', 'S'] else float(coord[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

def get_GPS():
    while True:
        ax, ay, az = bno.getVector(BNO055.VECTOR_ACCELEROMETER)
        squ_a = ax ** 2 + ay ** 2 + az ** 2
        size_a = math.sqrt(squ_a)
        print(f"総加速度の大きさ：{size_a}m/s^2")
        time.sleep(0.2)
        (count, data) = pi.bb_serial_read(RX_PIN)
        if count and data:
            text = data.decode("ascii", errors="ignore")
            if "$GNRMC" in text:
                lines = text.split("\n")
                for line in lines:
                    if "$GNRMC" in line:
                        parts = line.strip().split(",")
                        if len(parts) > 6 and parts[2] == "A":
                            lat = convert_to_decimal(parts[3], parts[4])
                            lon = convert_to_decimal(parts[5], parts[6])
                            return lat, lon     
    time.sleep(0.2)

for i in range(10):
    init_L76X()
    gps_lat_lon = get_GPS()
    print(f"{gps_lat_lon}")
