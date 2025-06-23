import serial
import time

im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

for i in range(10):
    data = f'TEST{i:02}'
    msg = f"TXDU 0003,{data}\r\n"
    im920.write(msg.encode())
    print(f"送信: {msg.strip()}")

    # 応答確認（ここが重要！！）
    time.sleep(0.2)
    response = im920.readline().decode(errors="ignore").strip()
    print(f"応答: {response}")

    time.sleep(1)
