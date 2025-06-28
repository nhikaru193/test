import smbus
import time

i2c = smbus.SMBus(1)
address = 0x76  # または 0x77

time.sleep(1)  # 電源投入直後の安定待ち

try:
    chip_id = i2c.read_byte_data(address, 0xD0)
    print(f"チップID: 0x{chip_id:02X}")
except Exception as e:
    print(f"読み取りエラー: {e}")
