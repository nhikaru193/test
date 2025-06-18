#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pigpio
import time

# 送受信に使う GPIO とボーレート設定（自由に変更可）
TX_PIN = 17    # BCM17 → L76XのRX へ接続
RX_PIN = 27    # BCM27 ← L76XのTX から受信
BAUD   = 9600  # 両方向とも 9600bps

# pigpio 初期化／デーモン接続確認
pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

# ソフトUART RX をビットバンギング受信で開く
err = pi.bb_serial_read_open(RX_PIN, BAUD, 8)
if err != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}, {BAUD}bps")
    pi.stop()
    exit(1)
print(f"▶ ソフトUART RX を開始：GPIO={RX_PIN}, {BAUD}bps")

# メインループ：受信データがあれば読み取り、送信処理も試す
try:
    while True:
        # ソフトUART RX で受信する
        (count, data) = pi.bb_serial_read(RX_PIN)
        if count and data:
            # Raw Bytes の表示
            print(f"<< Raw Bytes ({count}): {[hex(b) for b in data]}")

            # バイト列をASCII文字列に変換
            try:
                recv_str = data.decode("ascii", errors="ignore")
                print(f"<< Decoded Data: {recv_str.strip()}")
            except UnicodeDecodeError:
                pass

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
