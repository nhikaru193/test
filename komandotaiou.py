import serial
import time

# シリアルポートを開く（19200bps）
ser = serial.Serial('/dev/serial0', 19200, timeout=1)

# バージョン確認コマンドを送信
ser.write(b'VER\r\n')
time.sleep(0.5)

# 応答を受信
response = ser.read_all()
print(f'VER応答: {response}')
