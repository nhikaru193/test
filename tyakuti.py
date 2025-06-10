import smbus
import time
from bno055 import BNO055

# BME280関連
t_fine = 0.0
digT = []
digP = []
digH = []

i2c = smbus.SMBus(1)
address = 0x76

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
    return (t_fine * 5 + 128) / 256 / 100

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

# ----------- 着地判定処理 -----------

def check_landing(pressure_threshold=1010.0, acc_threshold=0.1, gyro_threshold=1.0, timeout=60):
    init_bme280()
    read_compensate()

    bno = BNO055()
    if not bno.begin():
        print("BNO055 初期化失敗")
        return
    bno.setExternalCrystalUse(True)
    bno.setMode(BNO055.OPERATION_MODE_NDOF)
    time.sleep(0.1)
    bno.getVector(BNO055.VECTOR_ACCELEROMETER)  # ウォームアップ
    time.sleep(0.1)

    print("🛬 着地判定開始")

    landing_counter = 0
    start_time = time.time()

    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                print("⏰ タイムアウト：強制判定")
                landing_counter += 1
                if landing_counter >= 3:
                    print("✅ 着地判定成功（タイムアウトで3回連続）")
                break

            pressure = read_pressure()
            acc_x, acc_y, acc_z = bno.getVector(BNO055.VECTOR_ACCELEROMETER)
            gyro_x, gyro_y, gyro_z = bno.getVector(BNO055.VECTOR_GYROSCOPE)

            print(f"[気圧] {pressure:.2f} hPa")
            print(f"[加速度] X: {acc_x:.2f}, Y: {acc_y:.2f}, Z: {acc_z:.2f} m/s²")
            print(f"[角速度] X: {gyro_x:.2f}, Y: {gyro_y:.2f}, Z: {gyro_z:.2f} °/s")

            acc_static = (abs(acc_x) < acc_threshold and
                          abs(acc_y) < acc_threshold and
                          abs(acc_z - 9.8) < acc_threshold)

            gyro_static = (abs(gyro_x) < gyro_threshold and
                           abs(gyro_y) < gyro_threshold and
                           abs(gyro_z) < gyro_threshold)

            pressure_ok = pressure > pressure_threshold  # 地上の気圧近辺想定

            if acc_static and gyro_static and pressure_ok:
                landing_counter += 1
                print(f"⚠️ 着地条件成立 {landing_counter}/3")
            else:
                landing_counter = 0

            if landing_counter >= 3:
                print("✅ 着地判定成功（3回連続成立）")
                break

            time.sleep(5)  # 測定間隔を5秒に設定

    except KeyboardInterrupt:
        print("⛔ 中断されました")
    finally:
        print("🔚 判定処理終了")

# 実行
check_landing(
    pressure_threshold=1010.0,
    acc_threshold=0.1,
    gyro_threshold=1.0,
    timeout=60
)
