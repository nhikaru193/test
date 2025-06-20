import serial
import time

im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

for i in range(10):
    data = f'TEST{i:02}'                 # → 6文字
    node = "0003"                        # 送信先ノード番号
    msg = "TXDA 0003,HELLO\r\n"
    im920.write(msg.encode())# ユニキャスト送信コマンド
    print(f"送信: {msg.strip()}")
    time.sleep(1)
