import serial
import time

# シリアルポートを開く（IM920が接続されたポートに合わせる）
im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

# 10回メッセージ送信
for i in range(10):
    msg = f"TXDA 0003,HELLO {i}\r\n"  # 宛先を0003に変更
    im920.write(msg.encode())
    print(f"送信: {msg.strip()}")

    # IM920の応答（例：OK や ERR）を読み取る（必要に応じて）
    response = im920.readline()
    print(f"応答: {response.decode().strip()}")

    time.sleep(1)
