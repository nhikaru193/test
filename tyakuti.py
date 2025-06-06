import time
import board
import busio
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_bno055

# I2C 初期化
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
bno = adafruit_bno055.BNO055_I2C(i2c, address=0x28)

# パラメータ
SAMPLE_INTERVAL = 0.5  # 秒
WINDOW_DURATION = 5    # 秒
SAMPLES_REQUIRED = int(WINDOW_DURATION / SAMPLE_INTERVAL)

# 閾値
PRESSURE_VARIATION_THRESHOLD = 0.2  # hPa
ACCEL_MEAN = 9.81  # m/s^2
ACCEL_VARIATION_THRESHOLD = 1.96  # ±0.2G
GYRO_THRESHOLD = 3  # deg/s

# 履歴バッファ
pressure_log = []
accel_log = []
gyro_log = []

def is_landed():
    # 気圧変化チェック
    if len(pressure_log) >= SAMPLES_REQUIRED:
        delta_pressure = max(pressure_log) - min(pressure_log)
        if delta_pressure > PRESSURE_VARIATION_THRESHOLD:
            return False

    # 加速度チェック（ベクトルの大きさ）
    accel_mags = [sum(x**2 for x in a)**0.5 for a in accel_log]
    if any(abs(mag - ACCEL_MEAN) > ACCEL_VARIATION_THRESHOLD for mag in accel_mags):
        return False

    # 角速度チェック（全軸）
    for gx, gy, gz in gyro_log:
        if abs(gx) > GYRO_THRESHOLD or abs(gy) > GYRO_THRESHOLD or abs(gz) > GYRO_THRESHOLD:
            return False

    return True

try:
    print("着地判定開始...")
    while True:
        # センサ読み取り
        pressure = bme280.pressure

        accel = bno.linear_acceleration
        if accel is None:
            accel = (0.0, 0.0, 0.0)

        gyro = bno.gyro
        if gyro is None:
            gyro = (0.0, 0.0, 0.0)

        # ログ保存
        pressure_log.append(pressure)
        accel_log.append(accel)
        gyro_log.append(gyro)

        # 過去のデータを切り捨て（5秒分に保つ）
        if len(pressure_log) > SAMPLES_REQUIRED:
            pressure_log.pop(0)
            accel_log.pop(0)
            gyro_log.pop(0)

        print(f"[測定] 気圧: {pressure:.2f} hPa, 加速度: {accel}, 角速度: {gyro}")

        # 着地判定
        if len(pressure_log) == SAMPLES_REQUIRED and is_landed():
            print("\n✅【着地判定】すべての条件を満たしました")
            break

        time.sleep(SAMPLE_INTERVAL)

except KeyboardInterrupt:
    print("\n[INFO] ユーザー中断")
