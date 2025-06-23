import serial
import RPi.GPIO as GPIO
import time

# シリアル設定
im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

# GPIOピン設定（GPIO22をワイヤレスグラウンド制御に使用）
wireless_PIN = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(wireless_PIN, GPIO.OUT)

# ユニキャスト送信関数
def send_unicast(node_id, payload):
    # ワイヤレスグラウンドON
    GPIO.output(wireless_PIN, GPIO.HIGH)
    print(f"GPIO{wireless_PIN} をHIGHに設定（ワイヤレスグラウンドON）")
    time.sleep(0.2)

    # コマンド送信
    cmd = f'TXDU {node_id},{payload}\r\n'
    im920.write(cmd.encode())
    print(f"送信: {cmd.strip()}")

    # 1秒以内に返ってくるはずの応答をすべて表示
    timeout = time.time() + 2
    while time.time() < timeout:
        if im920.in_waiting:
            res = im920.readline().decode(errors="ignore").strip()
            print("Response:", res)
        else:
            time.sleep(0.1)

# 実行
send_unicast("0003", "HELLO")
