import serial
import time

# IM920に接続（Raspberry PiのUARTポート）
im920 = serial.Serial('/dev/serial0', 19200, timeout=2)

for i in range(10):
    msg = f"TXDU 0003,HELLO {i}\r"  # ← ユニキャスト送信に修正
    im920.write(msg.encode())
    im920.flush()
    print(f"送信: {msg.strip()}")

    response = im920.readline()
    print(f"応答: {response.decode(errors='ignore').strip()}")

    time.sleep(1)
