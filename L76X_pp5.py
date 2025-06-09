import pigpio
import time

RX_PIN = 27
BAUD = 9600

pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

# RXポートをオープン
if pi.bb_serial_read_open(RX_PIN, BAUD, 8) != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}")
    pi.stop()
    exit(1)

print(f"▶ ソフトUART RX を開始：GPIO={RX_PIN}, {BAUD}bps")

recv_buffer = b""

try:
    while True:
        count, data = pi.bb_serial_read(RX_PIN)
        if count > 0:
            recv_buffer += data
            while b"\n" in recv_buffer:
                line, recv_buffer = recv_buffer.split(b"\n", 1)
                try:
                    decoded = line.decode("ascii", errors="ignore").strip()
                    if decoded.startswith("$GPRMC"):
                        print("✅ GPRMC:", decoded)
                    elif decoded.startswith("$"):
                        print("その他のNMEA:", decoded)
                except Exception as e:
                    print("デコードエラー:", e)
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
