import serial
import time

# UARTポートとボーレート設定（IM920のデフォルトは19200bps）
ser = serial.Serial('/dev/serial0', 19200, timeout=1)

# 子機に送るテストデータ
test_data = "TEST\r\n"

while True:
    ser.write(test_data.encode('utf-8'))
    print("送信：", test_data.strip())
    time.sleep(5)
