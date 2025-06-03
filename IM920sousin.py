import serial
import time

ser = serial.Serial('/dev/serial0', 19200, timeout=1)

# ---- コマンドモード突入手順（ガードタイムあり） ----
time.sleep(1.2)               # ガードタイム前
ser.write(b'+++')             # 改行なしで送ること！
time.sleep(1.2)               # ガードタイム後

# 応答確認（なくても成功してる場合もある）
resp = ser.read_all()
print(f'+++応答: {resp}')

# ---- 設定コマンド ----
ser.write(b'STNN 0001\r')     # 親機のネットワークアドレス
time.sleep(0.5)
print(f'STNN応答: {ser.read_all()}')

ser.write(b'STSN 0002\r')     # ノード番号
time.sleep(0.5)
print(f'STSN応答: {ser.read_all()}')

# ---- データ送信 ----
ser.write(b'TXDA Hello from Pi\r')
