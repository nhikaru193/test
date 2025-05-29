import serial
import time

# シリアルポートの設定
serial_port = '/dev/ttyAMA0'  # 使用するシリアルポートのパス
baud_rate = 19200  # ボーレート

# シリアルポートの初期化
ser = serial.Serial(serial_port, baud_rate, timeout=3)

def send_message(message):
    # メッセージの送信
    cmd = f'SENDB="{message}"\r\n'
    ser.write(cmd.encode('utf-8'))
    response = ser.readline().decode('utf-8').strip()
    if response == 'OK':
        print('Message sent successfully.')
    else:
        print(f'Failed to send message. Response: {response}')

# メッセージの送信例
message = 'Hello, IM920!'
send_message(message)

# シリアルポートのクローズa
ser.close()
