import smbus

i2c = smbus.SMBus(1)

for addr in [0x76, 0x77]:
    try:
        chip_id = i2c.read_byte_data(addr, 0xD0)
        print(f"I2Cアドレス 0x{addr:02X} のチップID: 0x{chip_id:02X}")
        if chip_id == 0x60:
            print("✅ このアドレスはBME280です！")
        else:
            print("⚠️ チップIDが0x60ではありません")
    except Exception as e:
        print(f"❌ アドレス0x{addr:02X} でエラー: {e}")
