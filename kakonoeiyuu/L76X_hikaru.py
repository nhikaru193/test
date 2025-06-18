#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pigpio
import time

# ─────────────────────────────────────────────────────────
# 送受信に使う GPIO とボーレート設定
# ─────────────────────────────────────────────────────────

TX_PIN = 17    # BCM17 → L76KのRX
RX_PIN = 27    # BCM27 ← L76KのTX
BAUD   = 9600  # 通常9600bps

# ─────────────────────────────────────────────────────────
# pigpio 初期化／デーモン接続確認
# ─────────────────────────────────────────────────────────

pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

# ─────────────────────────────────────────────────────────
# ソフトUART RX を開く
# ─────────────────────────────────────────────────────────

err = pi.bb_serial_read_open(RX_PIN, BAUD, 8)
if err != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}, {BAUD}bps")
    pi.stop()
    exit(1)
print(f"▶ ソフトUART RX を開始：GPIO={RX_PIN}, {BAUD}bps")

# ─────────────────────────────────────────────────────────
# メインループ
# ─────────────────────────────────────────────────────────

try:
    while True:
        (count, data) = pi.bb_serial_read(RX_PIN)
        if count > 0 and data:
            # 生データ（バイト列）をそのまま表示
            print(f"[Raw Bytes] {data}")

            try:
                recv_str = data.decode("ascii", errors="ignore")
                # 複数行に分けてNMEAセンテンスを表示
                lines = recv_str.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("$"):
                        print("<< NMEA Sentence:", line)
            except Exception as e:
                print("デコードエラー:", e)

        time.sleep(1.0)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
