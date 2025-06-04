commands = [
    b'VER\r\n',
    b'STNN 0001\r\n',
    b'STSN 0002\r\n',
    b'STPC 13\r\n',
    b'STPO 10\r\n',
    b'STGE 0\r\n',
    b'RINI\r\n',
    b'TXDA Hello Test\r\n'
]

import serial
import time

ser = serial.Serial('/dev/serial0', 19200, timeout=1)

for cmd in commands:
    print(f'Sending: {cmd.strip()}')
    ser.write(cmd)
    time.sleep(0.3)
    print(f'Response: {ser.read_all()}')
