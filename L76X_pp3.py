import pigpio
import time
import re

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
# ソフトUART RX をビットバンギング受信で開く
# ─────────────────────────────────────────────────────────

err = pi.bb_serial_read_open(RX_PIN, BAUD, 8)
if err != 0:
    print(f"ソフトUART RX の設定に失敗：GPIO={RX_PIN}, {BAUD}bps")
    pi.stop()
    exit(1)
print(f"▶ ソフトUART RX を開始：GPIO={RX_PIN}, {BAUD}bps")

def parse_gga(nmea_string):
    """
    $GNGGA,NMEA文を解析して緯度、経度などの情報を返す
    """
    pattern = r"\$GNGGA,(\d{6}\.\d{3}),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+)"
    match = re.match(pattern, nmea_string)
    
    if match:
        latitude = match.group(2)
        longitude = match.group(3)

        # 緯度と経度が有効な場合のみ返す
        if latitude and longitude and latitude != "0" and longitude != "0":
            return [latitude, longitude]
    return None

def parse_rmc(nmea_string):
    """
    $GNRMC,NMEA文を解析して緯度、経度、速度、日付などの情報を返す
    """
    pattern = r"\$GNRMC,(\d{6}\.\d{3}),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+)"
    match = re.match(pattern, nmea_string)
    
    if match:
        latitude = match.group(2)
        longitude = match.group(3)

        # 緯度と経度が有効な場合のみ返す
        if latitude and longitude and latitude != "0" and longitude != "0":
            return [latitude, longitude]
    return None

# ─────────────────────────────────────────────────────────
# メインループ：受信データがあれば読み取り、送信処理も試す
# ─────────────────────────────────────────────────────────

try:
    while True:
        # 受信データ
        (count, data) = pi.bb_serial_read(RX_PIN)
        
        if count and data:
            recv_str = data.decode("ascii", errors="ignore")
            print(f"<< SoftUART Received ({count}bytes):", recv_str.strip())

            # GGAメッセージの解析
            if recv_str.startswith("$GNGGA"):
                coords = parse_gga(recv_str)
                if coords:
                    print(f"緯度と経度: {coords}")  # [緯度, 経度] の形で出力
            
            # RMCメッセージの解析
            elif recv_str.startswith("$GNRMC"):
                coords = parse_rmc(recv_str)
                if coords:
                    print(f"緯度と経度: {coords}")  # [緯度, 経度] の形で出力
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nユーザー割り込みで終了します。")

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
    print("終了しました。")
