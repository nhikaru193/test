import serial
import time
import pigpio
import struct

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
    # 度分（ddmm.mmmm）形式を10進数に変換
    degrees = int(coord[:2]) if direction in ['N', 'S'] else int(coord[:3])
    minutes = float(coord[2:]) if direction in ['N', 'S'] else float(coord[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

im920 = serial.Serial('/dev/serial0', 19200, timeout=1)

buffer = b''

try:
    while True:
        # 受信処理
        (count, data) = pi.bb_serial_read(RX_PIN)
        if count and data:
            buffer += data
            # 受信バッファに "TXDA 0003," があるか探す
            start = buffer.find(b'TXDA 0003,')
            if start != -1:
                # "TXDA 0003," のあとに16バイト（緯度経度のdouble）あるか確認
                needed_len = start + len(b'TXDA 0003,') + 16
                if len(buffer) >= needed_len:
                    data_start = start + len(b'TXDA 0003,')
                    bin_data = buffer[data_start:data_start+16]

                    # バイナリ16バイトをdouble2つに変換（リトルエンディアン）
                    lat, lon = struct.unpack('<dd', bin_data)
                    print(f"受信 緯度: {lat:.8f}, 経度: {lon:.8f}")

                    # 処理済みデータをバッファから削除
                    buffer = buffer[data_start+16:]

        # GPSデータ読み込みと送信
        try:
            # pi.bb_serial_readは非同期なので、別のポートなどからGPS NMEAを読んでいる想定
            # ここはあなたの元コードを踏襲
            (count, data) = pi.bb_serial_read(RX_PIN)
            if count and data:
                text = data.decode("ascii", errors="ignore")
                if "$GNRMC" in text:
                    lines = text.split("\n")
                    for line in lines:
                        if "$GNRMC" in line:
                            parts = line.strip().split(",")
                            if len(parts) > 6 and parts[2] == "A":
                                lat = convert_to_decimal(parts[3], parts[4])
                                lon = convert_to_decimal(parts[5], parts[6])

                                # バイナリ形式で送信
                                data_bin = struct.pack('<dd', lat, lon)
                                msg = b'TXDA 0003,' + data_bin + b'\r\n'
                                im920.write(msg)

                                print(f"送信 緯度: {lat:.8f}, 経度: {lon:.8f}")
                                time.sleep(2)

        except Exception as e:
            print("デコードエラー:", e)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
