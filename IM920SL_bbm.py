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
    # ワイヤレスグラウンドON（HIGH）
    GPIO.output(wireless_PIN, GPIO.HIGH)
    print(f"GPIO{wireless_PIN} をHIGHに設定（ワイヤレスグラウンドON）")
    time.sleep(0.2)  # 安定のため少し待つ

    # TXDUコマンド送信
    cmd = f'TXDU {node_id},{payload}\r\n'
    im920.write(cmd.encode())
    print(f"送信: {cmd.strip()}")
    
    # 応答確認（オプション）
    time.sleep(0.5)
    while im920.in_waiting:
        res = im920.readline().decode().strip()
        print("Response:", res)

    # ワイヤレスグラウンドOFF（LOW）に戻す場合は以下を有効に
    # GPIO.output(wireless_PIN, GPIO.LOW)

# 実行
send_unicast("0003", "HELLO")
