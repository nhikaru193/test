import serial
import time

im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

for i in range(10):
    msg = f"HELLO {i}\r\n"  # 改行コード追加
    im920.write(msg.encode('ascii'))
    print(f"送信: {msg.strip()}")
    time.sleep(1)

