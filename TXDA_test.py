import serial
import time

# シリアルポートをIM920に接続した状態に
ser = serial.Serial('/dev/serial0', 19200, timeout=1)

# 遅延を入れて起動安定
time.sleep(2)

# テスト送信（← 改行は \r のみ）
msg = 'TXDA 0003,35.123456,139.654321\r'
ser.write(msg.encode('ascii'))
print("送信:", msg)
