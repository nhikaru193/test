import serial
import time

ser = serial.Serial('/dev/serial0', 19200, timeout=1)

# ---- 設定コマンド ----
ser.write(b'STNN 0001\r\n')     # 親機のネットワークアドレス
time.sleep(0.2)
print(f'STNN応答: {ser.read_all()}')

ser.write(b'STSN 0002\r\n')     # ノード番号
time.sleep(0.2)
print(f'STSN応答: {ser.read_all()}')

# 設定を反映（RINI = reboot）
ser.write(b'RINI\r\n')
time.sleep(0.5)
print(f'RINI応答: {ser.read_all()}')

# ---- データ送信 ----
ser.write(b'TXDA Hello from Pi\r\n')
print("データ送信完了")
