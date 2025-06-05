#!/usr/bin/env python3
import pigpio
import serial
import threading
import time

# ──────────────────────────────────────────────
# ① ソフトUART(pigpio) と GPS(HW UART) の設定
# ──────────────────────────────────────────────

# --- pigpio に接続 ---
pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できませんでした。")
    exit(1)

# --- ソフトUART 用 GPIO (BCM 番号) ---
#    自由に空いている GPIO を指定できる
SOFT_UART_TX_PIN = 17  # 例: GPIO17
SOFT_UART_RX_PIN = 27  # 例: GPIO27

# --- ソフトUART のボーレート(9600 or 19200 推奨) ---
SOFT_BAUD = 9600

# --- ハードUART（GPS）用のデバイスとボーレート ---
#    /dev/serial0 は通常 /dev/ttyAMA0 にリンクされる
GPS_PORT = '/dev/serial0'
GPS_BAUD = 9600

# ──────────────────────────────────────────────
# ② pigpio を使ってソフトUART を開く
# ──────────────────────────────────────────────

# TX (bit‐banging) を開始
if pi.bb_serial_write_open(SOFT_UART_TX_PIN, SOFT_BAUD, 8) != 0:
    print("ソフトUART TX の設定に失敗: GPIO={}, {}bps".format(SOFT_UART_TX_PIN, SOFT_BAUD))
    pi.stop()
    exit(1)

# RX (bit‐banging) を開始
if pi.bb_serial_read_open(SOFT_UART_RX_PIN, SOFT_BAUD, 8) != 0:
    print("ソフトUART RX の設定に失敗: GPIO={}, {}bps".format(SOFT_UART_RX_PIN, SOFT_BAUD))
    pi.bb_serial_write_close(SOFT_UART_TX_PIN)
    pi.stop()
    exit(1)

print("▶ ソフトUART を開始しました: TX GPIO={}, RX GPIO={}, {}bps".format(
    SOFT_UART_TX_PIN, SOFT_UART_RX_PIN, SOFT_BAUD))


# ──────────────────────────────────────────────
# ③ GPS 取得用のスレッド（pyserial）
# ──────────────────────────────────────────────

def gps_reader_thread():
    """
    ハードUART(/dev/serial0) 経由で GPS の NMEA データを読み取り続けるスレッド
    """
    try:
        ser = serial.Serial(GPS_PORT, GPS_BAUD, timeout=1.0)
    except serial.SerialException as e:
        print("GPS シリアルポートを開けませんでした:", e)
        return

    print("▶ GPS リーダースレッドを開始: ポート={} {}bps".format(GPS_PORT, GPS_BAUD))

    while True:
        try:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if not line:
                continue
            # NMEA の先頭が '$' の行だけ処理する
            if line.startswith('$'):
                # 例: $GPRMC,hhmmss.AAA,A,緯度,N,経度,E,...
                #      $GPGGA,hhmmss.AAA,緯度,N,経度,E,固定,衛星数,...
                print("<< GPS NMEA:", line)
                # 必要に応じてパースする → 例: NMEA ライブラリを使う
                # ここではとりあえず raw 出力のみ
        except Exception as e:
            print("GPS 読み取りエラー:", e)
            break

    ser.close()


# ──────────────────────────────────────────────
# ④ メイン処理：ソフトUART 送受信機能と GPS スレッド立ち上げ
# ──────────────────────────────────────────────

def main():
    # GPS 読み取りスレッドをデーモンモードで起動
    gps_thread = threading.Thread(target=gps_reader_thread, daemon=True)
    gps_thread.start()

    print("▶ メインループ開始: ソフトUART <-> 外部デバイス & GPS 並行取得")

    try:
        while True:
            # ----[ ソフトUART の送信例 ]----
            msg = "Hello Pi\n"
            pi.bb_serial_write(SOFT_UART_TX_PIN, msg.encode('utf-8'))
            print(">> SoftUART Sent:", msg.strip())

            # ----[ ソフトUART の受信例 ]----
            (count, data) = pi.bb_serial_read(SOFT_UART_RX_PIN)
            if count and data:
                recv = data.decode('utf-8', errors='ignore').strip()
                print("<< SoftUART Received:", recv)

            # ----[ 1 秒待機 ]----
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n※ ユーザーが割り込み (Ctrl+C) を実行しました。終了処理を行います …")

    # 終了時のクリーンアップ
    pi.bb_serial_read_close(SOFT_UART_RX_PIN)
    pi.bb_serial_write_close(SOFT_UART_TX_PIN)
    pi.stop()
    print("▶ ソフトUART および GPS スレッドを終了しました。")


if __name__ == '__main__':
    main()
