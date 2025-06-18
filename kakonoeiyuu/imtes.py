import serial
import time

im920 = serial.Serial('/dev/serial0', 19200, timeout=2)

# コマンドモードに入っているか不安なら最初にENWR
im920.write(b"ENWR\r")
time.sleep(0.1)

# 宛先0003へユニキャスト送信
im920.write(b"TXDU 0003,1234\r")
im920.flush()

# 応答を複数回試みて取得
for _ in range(5):
    resp = im920.readline()
    if resp:
        print("応答:", resp.decode(errors='ignore').strip())
        break
    time.sleep(0.2)
