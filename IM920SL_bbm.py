import serial
import time

ser = serial.Serial('/dev/serial0', 19200, timeout=1)

def send_cmd(cmd, wait=0.5):
    ser.write((cmd + '\r\n').encode())
    time.sleep(wait)
    response = ser.read_all().decode(errors='ignore')
    print(f"Sent: {cmd} | Response: {response}")
    return response

try:
    # 1. ワイヤレスグラウンドON
    send_cmd('WGON')

    # 2. 設定保存
    send_cmd('WRIT')

    # 3. 再起動
    send_cmd('RESET')
    time.sleep(3)  # 再起動待ち

    # 4. 子機（例：ノード0003）へユニキャスト送信
    # 送信コマンド例（モジュールによって異なります）
    send_cmd('TXDU 0003,Hello World')

    # 5. 送信成功かどうか応答を確認
    # ここで応答を解析し必要に応じて再送など行う

finally:
    ser.close()
