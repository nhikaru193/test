import smbus
import time
from BNO055 import BNO055

# BME280関連のグローバル変数
t_fine = 0.0
digT = []
digP = []
digH = []

# I2Cアドレスとバス設定
i2c = smbus.SMBus(1)
address = 0x76

# ----------- BME280 初期化と補正関数群（あなたのコードそのまま） -----------

def init_bme280():
    i2c.write_byte_data(address, 0xF2, 0x01)
    i2c.write_byte_data(address, 0xF4, 0x27)
    i2c.write_byte_data(address, 0xF5, 0xA0)

def read_compensate():
    global digT, digP, digH
    dat_t = i2c.read_i2c_block_data(address, 0x88, 6)
    digT = [(dat_t[1] << 8) | dat_t[0], (dat_t[3] << 8) | dat_t[2], (dat_t[5] << 8) | dat_t[4]]
    for i in range(1, 2):
        if digT[i] >= 32768:
            digT[i] -= 65536
    dat_p = i2c.read_i2c_block_data(address, 0x8E, 18)
    digP = [(dat_p[i+1] << 8) | dat_p[i] for i in range(0, 18, 2)]
    for i in range(1, 8):
        if digP[i] >= 32768:
            digP[i] -= 65536
    dh = i2c.read_byte_data(address, 0xA1)
    dat_h = i2c.read_i2c_block_data(address, 0xE1, 8)
    digH = [dh, (dat_h[1] << 8) | dat_h[0], dat_h[2],
            (dat_h[3] << 4) | (0x0F & dat_h[4]),
            (dat_h[5] << 4) | ((dat_h[4] >> 4) & 0x0F),
            dat_h[6]]
    if digH[1] >= 32768:
        digH[1] -= 65536
    for i in range(3, 4):
        if digH[i] >= 32768:
            digH[i] -= 65536
    if digH[5] >= 128:
        digH[5] -= 256

def bme280_compensate_t(adc_T):
    global t_fine
    var1 = (adc_T / 8.0 - digT[0] * 2.0) * digT[1] / 2048.0
    var2 = ((adc_T / 16.0 - digT[0]) ** 2) * digT[2] / 16384.0
    t_fine = var1 + var2
    t = (t_fine * 5 + 128) / 256 / 100
    return t

def bme280_compensate_p(adc_P):
    global t_fine
    var1 = t_fine - 128000.0
    var2 = var1 * var1 * digP[5]
    var2 += (var1 * digP[4]) * 131072.0
    var2 += digP[3] * 3.435973837e10
    var1 = (var1 * var1 * digP[2]) / 256.0 + (var1 * digP[1]) * 4096
    var1 = (1.407374884e14 + var1) * (digP[0] / 8589934592.0)
    if var1 == 0:
        return 0
    p = (1048576.0 - adc_P) * 2147483648.0 - var2
    p = (p * 3125) / var1
    var1 = digP[8] * (p / 8192.0)**2 / 33554432.0
    var2 = digP[7] * p / 524288.0
    p = (p + var1 + var2) / 256 + digP[6] * 16.0
    return p / 256 / 100

def read_pressure():
    dat = i2c.read_i2c_block_data(address, 0xF7, 8)
    dat_p = (dat[0] << 16 | dat[1] << 8 | dat[2]) >> 4
    dat_t = (dat[3] << 16 | dat[4] << 8 | dat[5]) >> 4
    bme280_compensate_t(dat_t)
    return bme280_compensate_p(dat_p)

# ----------- 放出判定処理 -----------

def check_release(pressure_threshold=900.0, acc_threshold=3.0, timeout=60):
    # BME280初期化
    init_bme280()
    read_compensate()
    
    from BNO055 import BNO055

# BNO055初期化部分
bno = BNO055.BNO055()  # BNO055クラスが正しく呼ばれているか
if not bno.begin():
    print("BNO055 初期化失敗")
    return
bno.setExternalCrystalUse(True)


    print("放出判定開始")

    release_counter = 0
    start_time = time.time()

    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                # タイムアウト時に放出判定を強制的に行う
                print("⏰ タイムアウト：判定中止")
                release_counter += 1
                print(f"⚠️ 判定成立 {release_counter}/3 - タイムアウトによる強制判定")
                if release_counter >= 3:
                    print("✅ 放出判定成功：タイムアウトで3回連続成立！")
                    break
                else:
                    break  # タイムアウト後ループ終了

            pressure = read_pressure()
            acc_x, acc_y, acc_z = bno.getVector(BNO055.VECTOR_LINEARACC)

            print(f"[気圧] {pressure:.2f} hPa, [加速度Z] {acc_z:.2f} m/s²")

            if pressure < pressure_threshold and abs(acc_z) > acc_threshold:
                release_counter += 1
                print(f"⚠️ 判定成立 {release_counter}/3")
            else:
                release_counter = 0

            if release_counter >= 3:
                print("✅ 放出判定成功：3回連続成立！")
                break

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("中断されました")
    finally:
        print("処理終了")

# 🔧 実行
check_release(pressure_threshold=890.0, acc_threshold=2.5, timeout=60)
