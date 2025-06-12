import pigpio
import time

TX_PIN = 17
RX_PIN = 27
BAUD = 9600

pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

err_tx = pi.bb_serial_write_open(TX_PIN, BAUD, 8)
if err_tx != 0:
    print(f"ソフトUART TX の設定に失敗：GPIO={TX_PIN}, {BAUD}bps")
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    exit(1)

print(f"▶ ソフトUART RX を開始：GPIO={RX_PIN}, {BAUD}bps")

def convert_to_decimal(coord, direction):
    degrees = int(coord[:2]) if direction in ['N', 'S'] else int(coord[:3])
    minutes = float(coord[2:]) if direction in ['N', 'S'] else float(coord[3:])
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
                            print(f"送信: 緯度={lat}, 経度={lon}")
                            msg = f"{lat},{lon}\r\n"
                            pi.bb_serial_write(TX_PIN, msg.encode())
                            time.sleep(1)  # 1秒待って次を受信
                            break  # 1つ処理したら次のループへ

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
