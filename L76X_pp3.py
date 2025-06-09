#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pigpio
import time

# ──────────────── 設定 ────────────────
TX_PIN = 17    # TX 未使用でもOK
RX_PIN = 27    # GPS TX → GPIO27
BAUD   = 9600  # ボーレート

# ────── pigpio 初期化 ──────
pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

err = pi.bb_serial_read_open(RX_PIN, BAUD, 8)
if err != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}, {BAUD}bps")
    pi.stop()
    exit(1)
print(f"▶ ソフトUART RX を開始：GPIO={RX_PIN}, {BAUD}bps")

# ────── 緯度・経度を10進数に変換 ──────
def convert_to_decimal(degree_min, direction):
    if not degree_min or not direction:
        return None
    if '.' not in degree_min:
        return None
    d, m = degree_min.split('.', 1)
    if len(d) <= 2:  # 例外的
        deg = int(d)
        minutes = float('0.' + m) * 60
    else:
        deg = int(d[:-2])
        minutes = float(d[-2:] + '.' + m)
    decimal = deg + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

# ────── メインループ ──────
try:
    buffer = ""
    while True:
        (count, data) = pi.bb_serial_read(RX_PIN)
        if count > 0:
            text = data.decode("ascii", errors="ignore")
            buffer += text

            # センテンスごとに分割
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()

                # デバッグ出力（オプション）
                # print("<<", line)

                # `$GNRMC` の有効なセンテンスを解析
                if line.startswith("$GNRMC") and ',A,' in line:
                    fields = line.split(',')
                    if len(fields) > 6:
                        lat = convert_to_decimal(fields[3], fields[4])
                        lon = convert_to_decimal(fields[5], fields[6])
                        if lat is not None and lon is not None:
                            x = [lat, lon]
                            print("緯度と経度 (10進数):", x)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
