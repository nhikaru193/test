import serial
import time

im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

for i in range(10):
    data = f'TEST{i:02}'
    msg = f'TXDA 0003,{data}\r\n'
    im920.write(msg.encode())
    print(f"送信: {msg.strip()}")
    time.sleep(1)
