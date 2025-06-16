import serial
import time

im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

for i in range(10):
    msg = f"TXDA 0001,HELLO {i}\r\n"
    im920.write(msg.encode())
    print(f"送信: {msg}")
    time.sleep(1)
