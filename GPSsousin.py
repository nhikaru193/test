import pigpio
import time

# ピン設定
RX_PIN = 27  # GPSのデータを受信（Raspberry Piの受信＝GPSのTX）
TX_PIN = 17  # IM920SLへ送信（Raspberry Piの送信＝IM920SLのRX）

# 通信速度設定
GPS_BAUD = 9600
IM920_BAUD = 19200

# pigpio接続
pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

# GPS用 RXピン初期化
if pi.bb_serial_read_open(RX_PIN, GPS_BAUD, 8) != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}, {GPS_BAUD}bps")
    pi.stop()
    exit(1)

# IM920SL用 TXピン初期化
if pi.bb_serial_write_open(TX_PIN, IM920_BAUD, 8) != 0:
    print(f"ソフトUART TX の設定に失敗：GPIO={TX_PIN}, {IM920_BAUD}bps")
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    exit(1)

print("▶ GPS受信・IM920SL送信を開始")

def convert_to_decimal(coord, direction):
    # ddmm.mmmm → 10進数に変換
    if direction in ['N', 'S']:
        degrees = int(coord[:2])
        minutes = float(coord[2:])
    else:
        degrees = int(coord[:3])
        minutes = float(coord[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

buffer = ""

try:
    while True:
        (count, data) = pi.bb_serial_read(RX_PIN)
        if count and data:
            try:
                buffer += data.decode("ascii", errors="ignore")
                lines = buffer.split("\n")
                buffer = lines[-1]  # 最後の不完全な行を残す

                for line in lines[:-1]:
                    if "$GNRMC" in line:
                        parts = line.strip().split(",")
                        if len(parts) > 6 and parts[2] == "A":
                            lat = convert_to_decimal(parts[3], parts[4])
                            lon = convert_to_decimal(parts[5], parts[6])
                            msg = f"{lat:.6f},{lon:.6f}\r\n"
                            print("送信:", msg.strip())
                            pi.bb_serial_write(TX_PIN, msg.encode("ascii"))
                            time.sleep(1)  # 1秒おきに送信
                            break  # 一つだけ送ってループに戻る

            except Exception as e:
                print("デコードエラー:", e)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.bb_serial_write_close(TX_PIN)
    pi.stop()
    print("終了しました。")
