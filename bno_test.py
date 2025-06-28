import smbus

i2c = smbus.SMBus(1)

for addr in [0x28, 0x29]:
    try:
        chip_id = i2c.read_byte_data(addr, 0x00)
        print(f"I2Cアドレス0x{addr:02X} のチップID: 0x{chip_id:02X}")
        if chip_id == 0xA0:
            print("✅ BNO055がこのアドレスにいます！")
        else:
            print("⚠️ 読み取れたが、チップIDが0xA0ではありません。")
    except Exception as e:
        print(f"❌ アドレス0x{addr:02X} でエラー: {e}")
