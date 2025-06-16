import serial
import time

im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

for i in range(10):
    data = f'TEST{i:02}'                 # → 6文字
    length = len(data)                   # → 6
    msg = f'TXDA {length:04},{data}\r\n' # → 'TXDA 0006,TEST00\r\n'
    im920.write(msg.encode())
    print(f"送信: {msg.strip()}")
    time.sleep(1)
