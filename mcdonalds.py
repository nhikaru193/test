import serial
import time
import pigpio

# ----- pigpio での入力設定（変更なし） -----
TX_PIN = 27
RX_PIN = 17
BAUD = 9600

pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

err = pi.bb_serial_read_open(RX_PIN, BAUD, 8)
if err != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}, {BAUD}bps")
    pi.stop()
    exit(1)

print(f"▶ ソフトUART RX を開始：GPIO={RX_PIN}, {BAUD}bps")

def convert_to_decimal(coord, direction):
    # 度分（ddmm.mmmm）→ 10進数
    deg = int(coord[:2]) if direction in ['N','S'] else int(coord[:3])
    minute = float(coord[2:]) if direction in ['N','S'] else float(coord[3:])
    dec = deg + minute/60
    return -dec if direction in ['S','W'] else dec

# Im920 用シリアル
im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

# Tera Term (PC) 用シリアル
# USB–TTL アダプタだったら '/dev/ttyUSB0'、ガジェットなら '/dev/ttyGS0' など
pc = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

try:
    while True:
        count, data = pi.bb_serial_read(RX_PIN)
        if count and data:
            text = data.decode('ascii', errors='ignore')
            if '$GNRMC' in text:
                for line in text.split('\n'):
                    if line.startswith('$GNRMC'):
                        parts = line.split(',')
                        if len(parts) > 6 and parts[2] == 'A':
                            lat = convert_to_decimal(parts[3], parts[4])
                            lon = convert_to_decimal(parts[5], parts[6])

                            # ❶ 10進数を小数点以下 6 桁までカンマ区切り文字列に整形
                            coord_str = f"{lat:.6f},{lon:.6f}\r\n"

                            # ❷ Im920 に送信（必要ならそのまま）
                            tx_msg = f"TXDA 0003,{coord_str}"
                            im920.write(tx_msg.encode())

                            # ❸ PC（Tera Term）に送信
                            pc.write(coord_str.encode())

                            # オプション：コンソールにも出力
                            print("TeraTerm →", coord_str.strip())

                            time.sleep(2)
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    im920.close()
    pc.close()
    print("終了しました。")
