import time
import board
import busio
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_bno055

# I2C初期化
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
bno = adafruit_bno055.BNO055_I2C(i2c, address=0x28)

# 閾値設定
PRESSURE_THRESHOLD = 950     # hPa
ACCEL_THRESHOLD = 2.5 * 9.81 # m/s²
TIMEOUT_SEC = 180            # 3分
STABILITY_CHECK_INTERVAL = 20 # 変化がないときの閾値（秒）
REQUIRED_CONSECUTIVE_COUNT = 3

# 状態記録
start_time = time.time()
last_change_time = start_time
last_pressure = None
last_accel = None

# 判定バッファ
consecutive_success_count = 0

def log_release(reason="不明"):
    print(f"[放出判定] 条件達成 - 理由: {reason}")

try:
    while True:
        now = time.time()

        # センサ読み取り
        try:
            pressure = bme280.pressure
        except Exception as e:
            print(f"[ERROR] 気圧読み込み失敗: {e}")
            pressure = None

        try:
            accel = bno.linear_acceleration
            if accel is not None:
                total_accel = sum(x**2 for x in accel if x is not None) ** 0.5
            else:
                total_accel = None
        except Exception as e:
            print(f"[ERROR] 加速度読み込み失敗: {e}")
            total_accel = None

        print(f"気圧: {pressure} hPa, 加速度: {total_accel} m/s²")

        # 放出条件チェック（連続3回）
        if pressure is not None and total_accel is not None:
            if pressure < PRESSURE_THRESHOLD and total_accel > ACCEL_THRESHOLD:
                consecutive_success_count += 1
                print(f"[INFO] 条件成立カウント: {consecutive_success_count}/{REQUIRED_CONSECUTIVE_COUNT}")
                if consecutive_success_count >= REQUIRED_CONSECUTIVE_COUNT:
                    log_release("気圧＆加速度が3回連続で条件成立")
                    break
            else:
                consecutive_success_count = 0  # 条件外ならリセット

        # 判定：センサ変化が止まった
        if last_pressure is not None and last_accel is not None:
            if abs(pressure - last_pressure) > 0.01 or abs(total_accel - last_accel) > 0.1:
                last_change_time = now

        last_pressure = pressure
        last_accel = total_accel

        if now - last_change_time > STABILITY_CHECK_INTERVAL:
            log_release("センサ変化停止（異常またはフリーズ）")
            break

        if now - start_time > TIMEOUT_SEC:
            log_release("タイムアウトによるフェールセーフ")
            break

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n[INFO] ユーザー中断")
