import serial
import time

ser = serial.Serial('/dev/serial0', 19200, timeout=1)

# ガードタイム：送信前に1秒待つ
time.sleep(1)
ser.write(b'+++')
time.sleep(1)  # ガードタイム（後）

print(ser.read_all())  # ← OKが出るかは状況次第（何も返らないことも）

# 親機アドレス（ネットワークアドレス）設定
ser.write(b'STNN 0001\r')
time.sleep(0.5)
print(ser.read_all())

# 自分のノード番号設定
ser.write(b'STSN 0002\r')
time.sleep(0.5)
print(ser.read_all())

# データ送信
ser.write(b'TXDA Hello from Pi\r')
