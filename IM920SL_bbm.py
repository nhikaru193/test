import serial
import time
import RPi.GPIO as GPIO

# GPIO設定
WIRE_GND_PIN = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(WIRE_GND_PIN, GPIO.OUT, initial=GPIO.LOW)

# IM920シリアル設定
im920 = serial.Serial('/dev/serial0', 19200, timeout=0.5)

print("IM920通信開始。'GND_ON'/'GND_OFF'でGPIO制御。'SEND:<メッセージ>'で送信。")

try:
    while True:
        line = im920.readline().decode(errors="ignore").strip()
        if line:
            print(f"受信: {line}")

            # GPIO制御
            if 'GND_ON' in line:
                print("GPIOをHIGHに設定")
                GPIO.output(WIRE_GND_PIN, GPIO.HIGH)
            elif 'GND_OFF' in line:
                print("GPIOをLOWに設定")
                GPIO.output(WIRE_GND_PIN, GPIO.LOW)

            # 無線送信コマンドを受信（例：SEND:HELLO）
            elif line.startswith('SEND:'):
                send_msg = line[5:]
                tx_cmd = f"TXDU 0003,{send_msg}\r\n"
                im920.write(tx_cmd.encode())
                print(f"送信コマンド送出: {tx_cmd.strip()}")

                # 応答待ち（任意）
                time.sleep(0.2)
                resp = im920.readline().decode(errors="ignore").strip()
                print(f"送信応答: {resp}")

except KeyboardInterrupt:
    print("終了処理。GPIOをLOWに戻します。")
    GPIO.output(WIRE_GND_PIN, GPIO.LOW)

finally:
    GPIO.cleanup()
    print("GPIOクリーンアップ完了")
