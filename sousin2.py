import serial
import time

ser = serial.Serial('/dev/serial0', 19200, timeout=1)

# データを1秒おきに送信
while True:
    msg = "Hello from Pi\r"
    ser.write(msg.encode('utf-8'))
    print("送信:", msg.strip())
    time.sleep(1)
