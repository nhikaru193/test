import serial
import RPi.GPIO as GPIO
import time

# IM920と接続されているシリアルポートと通信設定
im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

# GPIOのピン番号設定
# 回路図の「GPIO25」はBCMモードの25番ピンを指す
wireless_PIN = 22

# GPIOのモードをBCMに設定（GPIO番号で指定）
GPIO.setmode(GPIO.BCM)

# データを送信する関数
def send_unicast(node_id, payload):
    cmd = f'TXDU {node_id},{payload}\r\n'
    im920.write(cmd.encode())
    time.sleep(0.5)  # 応答待ち（必要なら調整）
    
    # 応答読み取り（オプション）
    while im920.in_waiting:
        print(f"GPIO{NICHROME_PIN} をHIGHに設定し、ニクロム線をオンにします。")
        GPIO.output(NICHROME_PIN, GPIO.HIGH)
        res = im920.readline().decode().strip()
        print("Response:", res)

# 実行例：ノード0003へ "HELLO" を送信
send_unicast("0003", "HELLO")
