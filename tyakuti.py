import smbus
import time
from bno055 import BNO055  # BNO055ライブラリをインポート

# BME280関連のグローバル変数
t_fine = 0.0
digT = []
digP = []
digH = []

# I2Cアドレスとバス設定
i2c = smbus.SMBus(1)
address = 0x76

# BME280 初期化と補正関数群（省略）

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

# 着地判定処理
def check_landing(pressure_threshold=1010.0, acc_threshold=0.05, timeout=60):
    # BME280初期化
    init_bme280()
    read_compensate()

    # BNO055初期化
    bno = BNO055()
    if not bno.begin():
        print("BNO055 初期化失敗")
        return
    bno.setExternalCrystalUse(True)
    bno.setMode(BNO055.OPERATION_MODE_NDOF)
    time.sleep(0.05)

    # ダミー読み取りでウォームアップ
    bno.getVector(BNO055.VECTOR_ACCELEROMETER)
    time.sleep(0.1)

    print("着地判定開始")

    landing_counter = 0
    start_time = time.time()

    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                # タイムアウト時に着地判定を強制的に行う
                print("⏰ タイムアウト：判定中止")
                landing_counter += 1
                print(f"⚠️ 判定成立 {landing_counter}/3 - タイムアウトによる強制判定")
                if landing_counter >= 3:
                    print("✅ 着地判定成功：タイムアウトで3回連続成立！")
                    break
                else:
                    break  # タイムアウト後ループ終了

            pressure = read_pressure()
            acc_x, acc_y, acc_z = bno.getVector(BNO055.VECTOR_ACCELEROMETER)

            # 加速度が静止状態に近いかつ気圧が一定で、角加速度も安定しているかを判定
            if abs(acc_x) < acc_threshold and abs(acc_y) < acc_threshold and abs(acc_z - 9.8) < acc_threshold:
                landing_counter += 1
                print(f"⚠️ 判定成立 {landing_counter}/3")
            else:
                landing_counter = 0

            if landing_counter >= 3:
                print("✅ 着地判定成功：3回連続成立！")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("中断されました")
    finally:
        print("処理終了")

# 実行
check_landing(pressure_threshold=1010.0, acc_threshold=0.05, timeout=60)
