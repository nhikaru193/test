import serial
import time

ser = serial.Serial('/dev/ttyS0', 19200, timeout=1)

print("+++ を送信（Enterなし）")
ser.write(b'+++')
time.sleep(2)

response = ser.read(64)
print("応答:", response.decode('utf-8', errors='ignore'))

ser.close()
