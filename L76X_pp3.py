# -*- coding: utf-8 -*-

import pigpio
import time

# ─────────────────────────────────────────────────────────
# 送受信に使う GPIO とボーレート設定（自由に変更可）
# ─────────────────────────────────────────────────────────

TX_PIN = 17    # BCM17 → L76XのRX へ接続
RX_PIN = 27    # BCM27 ← L76XのTX から受信
BAUD   = 9600  # 両方向とも 9600bps

# ─────────────────────────────────────────────────────────
# pigpio 初期化／デーモン接続確認
# ─────────────────────────────────────────────────────────

pi = pigpio.pi()
if not pi.connected:
    print("pigpio デーモンに接続できません。")
    exit(1)

# ─────────────────────────────────────────────────────────
# ソフトUART TX を wave 機能で使う準備
# ─────────────────────────────────────────────────────────

# （TX 側は wave_add_serial による波形送信を使うため特別な open は不要）

# ─────────────────────────────────────────────────────────
# ソフトUART RX をビットバンギング受信で開く
# ─────────────────────────────────────────────────────────

#   pigpio.bb_serial_read_open(GPIOnumber, baud, word_bits)
#   で「このピンを RX 専用のソフトUART」として開く
err = pi.bb_serial_read_open(RX_PIN, BAUD, 8)
if err != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}, {BAUD}bps")
    pi.stop()
    exit(1)
print(f"▶ ソフトUART RX を開始：GPIO={RX_PIN}, {BAUD}bps")

# ─────────────────────────────────────────────────────────
# メインループ：受信データがあれば読み取り、送信処理も試す
# ─────────────────────────────────────────────────────────

try:
    while True:
        # ------- [1] ソフトUART RX で受信する例 -------
        (count, data) = pi.bb_serial_read(RX_PIN)
        if count and data:
            # data はバイト列なので、文字列に変換
            recv_str = data.decode("ascii", errors="ignore")
            print(f"<< SoftUART Received ({count}bytes):", recv_str.strip())

            # 例：受信した NMEA ($GPRMC など) をそのまま wave 送信する
            # もし波形送信したいなら以下のように
            # pi.wave_clear()
            # pi.wave_add_serial(TX_PIN, BAUD, recv_str)
            # wid = pi.wave_create()
            # if wid >= 0:
            #     pi.wave_send_once(wid)
            #     while pi.wave_tx_busy():
            #         time.sleep(0.005)
            #     pi.wave_delete(wid)
            # print("→ リレー送信しました:", recv_str.strip())

        # ------- [2] 必要であれば、別メッセージを挟んで定期送信も可能 -------
        # ここでは特に何もしないか、1秒待機
        time.sleep(1.0)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    # ソフトUART RX をクローズしてリソース解放
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
