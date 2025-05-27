import serial
import time

# シリアルポートの設定
PORT = 'COM3'  # 環境に合わせて変更（macOS/Linuxでは例: '/dev/ttyUSB0'）
BAUDRATE = 19200  # IM920のデフォルト

# 送信する宛先とメッセージ、宛先は後で変える
NODE_ID = '0001'
MESSAGE = 'Hello, IM920!'

def send_data():
    with serial.Serial(PORT, BAUDRATE, timeout=1) as ser:
        print("Sending message to IM920SL...")
        while True:
            cmd = f'TXDA {NODE_ID} {MESSAGE}\r'
            ser.write(cmd.encode())
            print(f"Sent: {MESSAGE}")
            time.sleep(5)  # 5秒ごとに送信

if __name__ == "__main__":
    send_data()
