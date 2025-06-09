
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pigpio
import time

RX_PIN = 27
BAUD = 9600

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

try:
    while True:
        count, data = pi.bb_serial_read(RX_PIN)
        if count > 0:
            try:
                recv_str = data.decode("ascii")
            except UnicodeDecodeError:
                recv_str = "[デコード不可]"

            print(f"<< 受信 ({count}バイト): {recv_str.strip()}")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
