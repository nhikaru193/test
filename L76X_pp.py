#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pigpio
import time

TX_PIN = 27    # TX（未使用だが念のため指定）
RX_PIN = 17    # RX ← GPS TXD
BAUD   = 9600  # 9600 bps

pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

# RXのみビットバンギング受信を開始
if pi.bb_serial_read_open(RX_PIN, BAUD, 8) != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}")
    pi.stop()
    exit(1)

print(f"▶ SoftUART RX 開始：GPIO={RX_PIN}, {BAUD} bps")

def dm_to_deg(dm_str, hemi):
    """度分（DDMM.MMMM）→10進度、N/S/E/W判定"""
    if not dm_str or dm_str == "":
        return None
    d, m = int(dm_str[:-7]), float(dm_str[-7:])
    deg = d + m/60.0
    if hemi in ('S','W'):
        deg = -deg
    return deg

buffer = b""
try:
    while True:
        count, data = pi.bb_serial_read(RX_PIN)
        if count and data:
            buffer += data
            # 改行まで行を切り出す
            while b"\r\n" in buffer:
                line, buffer = buffer.split(b"\r\n", 1)
                try:
                    text = line.decode('ascii', errors='ignore')
                except:
                    continue
                if text.startswith('$GPRMC'):
                    # GPRMC: $GPRMC,hhmmss,A,lat,NS,lon,EW,...
                    parts = text.split(',')
                    if len(parts) > 6 and parts[2] == 'A':  # A = valid
                        lat = dm_to_deg(parts[3], parts[4])
                        lon = dm_to_deg(parts[5], parts[6])
                        print(f"<< GPRMC OK  緯度: {lat:.6f}, 経度: {lon:.6f}")
                    else:
                        print("<< GPRMC 無効データまたは欠損")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
