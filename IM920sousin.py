import serial
import time

ser = serial.Serial('/dev/serial0', 19200, timeout=1)

ser.write(b'+++')
time.sleep(1)
print(ser.read_all())

ser.write(b'STNN 0001\r')
time.sleep(0.5)
print(ser.read_all())

ser.write(b'STSN 0002\r')
time.sleep(0.5)

ser.write(b'TXDA Hello from Pi\r')
