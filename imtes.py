import serial
import time

im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

for i in range(10):
    msg = f"HELLO {i}"
    im920.write(msg.encode('ascii'))  # ASCII文字列を直接送信
    print(f"送信: {msg}")
    time.sleep(1)
