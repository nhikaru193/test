import smbus
import time

i2c = smbus.SMBus(1)
address = 0x76  # or 0x77

# ソフトリセット（0xB6を書き込む）
try:
    i2c.write_byte_data(address, 0xE0, 0xB6)
    print("✅ ソフトリセット送信済み")
    time.sleep(1.5)  # 初期化完了まで待機
except Exception as e:
    print(f"❌ ソフトリセット失敗: {e}")

# チップID再確認
try:
    chip_id = i2c.read_byte_data(address, 0xD0)
    print(f"チップID: 0x{chip_id:02X}")
except Exception as e:
    print(f"❌ チップID読み取りエラー: {e}")
