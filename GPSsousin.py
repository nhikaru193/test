import pigpio
import time

TX_PIN = 17  # IM920SLのRXDに接続
RX_PIN = 27  # GPSのTXに接続
GPS_BAUD = 9600
IM920_BAUD = 19200

pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

# GPS受信（GPIO27）をソフトUARTでオープン
if pi.bb_serial_read_open(RX_PIN, GPS_BAUD, 8) != 0:
    print("ソフトUART RXの設定に失敗しました。")
    pi.stop()
    exit(1)

print("▶ GPSの受信を開始")

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
                buffer = lines[-1]

                for line in lines[:-1]:
                    if "$GNRMC" in line:
                        parts = line.strip().split(",")
                        if len(parts) > 6 and parts[2] == "A":
                            lat = convert_to_decimal(parts[3], parts[4])
                            lon = convert_to_decimal(parts[5], parts[6])
                            msg = f"{lat},{lon}\r\n"
                            print(f"送信: {msg.strip()}")
                            pi.bb_serial_write(TX_PIN, msg.encode())
                            time.sleep(1)
                            break
            except Exception as e:
                print("デコードエラー:", e)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
