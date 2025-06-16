import serial
import time

# シリアルポートを開く
im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

for i in range(10):
    msg = f"TXDA 0003,HELLO {i}\r"  # ← \r のみに変更
    im920.write(msg.encode())
    im920.flush()  # 念のためフラッシュ
    print(f"送信: {msg.strip()}")

    response = im920.readline()
    print(f"応答: {response.decode(errors='ignore').strip()}")  # decode エラーも回避

    time.sleep(1)
