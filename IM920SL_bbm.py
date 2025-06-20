import serial
import time

im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

for i in range(10):
    data = f'TEST{i:02}'                 # → 6文字
    node = "0003"                        # 送信先ノード番号
    msg = f"TXDU {node},{data}\r\n"      # ✅ ユニキャスト送信コマンドに修正
    im920.write(msg.encode())
    print(f"送信: {msg.strip()}")
    time.sleep(1)
