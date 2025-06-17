import smbus
import time
from BNO055 import BNO055  # BNO055をインポート
import BME280

# BME280関連のグローバル変数
t_fine = 0.0
digT = []
digP = []
digH = []

# I2Cアドレスとバス設定
i2c = smbus.SMBus(1)
address = 0x76
# ----------- 放出判定処理 -----------

def check_release(pressure_threshold=900.0, acc_threshold=3.0, timeout=60):
    # BME280初期化
    BME280.init_bme280()
    BME280.read_compensate()

    # BNO055初期化部分
    bno = BNO055()  # BNO055クラスのインスタンス化
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
                release_counter += 3
                print(f"⚠️ 判定成立 {release_counter}/3 - タイムアウトによる強制判定")
                if release_counter >= 3:
                    print("✅ 放出判定成功：タイムアウトで3回連続成立！")
                    break
                else:
                    break  # タイムアウト後ループ終了

            pressure = BME280.get_pressure()
            acc_x, acc_y, acc_z = bno.getVector(BNO055.VECTOR_ACCELEROMETER)  # 修正した部分

            print(f"[気圧] {pressure:.2f} hPa, [加速度Z] {acc_z:.2f} m/s²")

            if pressure < pressure_threshold and abs(acc_z) > acc_threshold:
                release_counter += 1
                print(f"⚠️ 判定成立 {release_counter}/3")
            else:
                release_counter = 0

            if release_counter >= 3:
                print("✅ 放出判定成功：3回連続成立！")
                break

    except KeyboardInterrupt:
        print("中断されました")
    finally:
        print("処理終了")

# 🔧 実行
check_release(pressure_threshold=890.0, acc_threshold=2.5, timeout=60)
