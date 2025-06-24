import RPi.GPIO as GPIO
import time
import socket
from pynput import keyboard
import threading
import serial # pigpio.bb_serial_read_openは必要だが、serialモジュール自体はGPS読み取りには不要。
import pigpio

# motor.py から MotorDriver クラスをインポート
from motor import MotorDriver

# --- グローバル変数と初期設定 ---
# モーター制御ピン (ご自身の配線に合わせて変更してください)
# 例: L298Nなどのモータードライバーの場合を想定
PWMA = 12  # 左モーターの速度制御 (PWM)
AIN1 = 23  # 左モーターの方向制御1
AIN2 = 18  # 左モーターの方向制御2

PWMB = 19  # 右モーターの速度制御 (PWM)
BIN1 = 16  # 右モーターの方向制御1
BIN2 = 26  # 右モーターの方向制御2

STBY = 21  # スタンバイピン (モーターON/OFF)

# GPS (ソフトUART) 用のピンとボーレート
# ラズパイのGPIO17 (GPSモジュールのTXに接続)
GPS_RX_PIN = 17
GPS_BAUD = 9600

# グローバルなインスタンスと状態変数
motor = None
pi = None # pigpioインスタンス
current_action = "stop"
# 前回の速度を保持するための変数 (滑らかな加速/減速に使用)
last_speed = 0
target_speed = 50 # デフォルトの目標速度 (デューティ比 0-100)

# スレッド終了のためのイベント
exit_event = threading.Event()

# --- GPSデータ処理関数 ---
def convert_to_decimal(coord, direction):
    # 度分（ddmm.mmmm）形式を10進数に変換
    degrees = int(coord[:2]) if direction in ['N', 'S'] else int(coord[:3])
    minutes = float(coord[2:]) if direction in ['N', 'S'] else float(coord[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

# --- GPSデータ読み取りを担当するスレッド関数 ---
def gps_reader_thread():
    global pi # piインスタンスは共有

    print("GPSデータ読み取りスレッドを開始します...")

    # pigpioデーモンに接続
    pi = pigpio.pi()
    if not pi.connected:
        print("エラー: pigpio デーモンに接続できません。pigpiodが実行されているか確認してください。")
        exit_event.set() # メインスレッドに終了を通知
        return

    # ソフトUART RX の設定
    err = pi.bb_serial_read_open(GPS_RX_PIN, GPS_BAUD, 8)
    if err != 0:
        print(f"エラー: ソフトUART RX の設定に失敗：GPIO={GPS_RX_PIN}, {GPS_BAUD}bps, エラーコード: {err}")
        exit_event.set() # メインスレッドに終了を通知
        pi.stop()
        return

    print(f"▶ ソフトUART RX を開始：GPIO={GPS_RX_PIN}, {GPS_BAUD}bps")

    try:
        while not exit_event.is_set(): # 終了イベントがセットされるまでループ
            (count, data) = pi.bb_serial_read(GPS_RX_PIN)
            if count and data:
                try:
                    text = data.decode("ascii", errors="ignore")
                    if "$GNRMC" in text:
                        lines = text.split("\n")
                        for line in lines:
                            if "$GNRMC" in line:
                                parts = line.strip().split(",")
                                if len(parts) > 6 and parts[2] == "A": # "A"は有効なデータを示す
                                    try:
                                        lat = convert_to_decimal(parts[3], parts[4])
                                        lon = convert_to_decimal(parts[5], parts[6])
                                        print(f"GPSデータ受信: 緯度={lat:.6f}, 経度={lon:.6f}")
                                    except ValueError as ve:
                                        print(f"GPS座標の変換エラー: {ve}, ライン: {line.strip()}")
                                elif len(parts) <= 6: # length check for IndexError
                                    print(f"GPSデータフォーマットエラー (長さ不足): {line.strip()}")
                except UnicodeDecodeError as ude:
                    print(f"GPSデータデコードエラー: {ude}, データ: {data}")
                except Exception as e:
                    print(f"GPSデータ処理中に予期せぬエラー: {e}")
            time.sleep(0.1) # ポーリング間隔

    except Exception as e:
        print(f"GPSデータ読み取りスレッドでエラーが発生しました: {e}")
    finally:
        print("GPSデータ読み取りスレッドを終了します。クリーンアップ中...")
        if pi and pi.connected:
            pi.bb_serial_read_close(GPS_RX_PIN)
            pi.stop()
            print("pigpioリソースをクリーンアップしました。")

# --- キーボード入力処理 ---
def on_press(key):
    global current_action, last_speed, target_speed, motor

    if exit_event.is_set(): # 終了イベントがセットされていたら何もしない
        return

    try:
        # pynputのキーオブジェクトがchar属性を持つかチェック
        char_key = getattr(key, 'char', None)

        if char_key == 'w':
            if current_action != "forward":
                print(f"前進 (目標速度: {target_speed})")
                motor.changing_forward(last_speed, target_speed)
                current_action = "forward"
                last_speed = target_speed # 新しい現在の速度を記録
        elif char_key == 's':
            if current_action != "backward":
                print(f"後退 (目標速度: {target_speed})")
                motor.changing_retreat(last_speed, target_speed) # 後退も滑らかに
                current_action = "backward"
                last_speed = target_speed
        elif char_key == 'a':
            if current_action != "turn_left":
                print(f"左旋回 (目標速度: {target_speed})")
                motor.changing_left(last_speed, target_speed) # 左旋回も滑らかに
                current_action = "turn_left"
                last_speed = target_speed
        elif char_key == 'd':
            if current_action != "turn_right":
                print(f"右旋回 (目標速度: {target_speed})")
                motor.changing_right(last_speed, target_speed) # 右旋回も滑らかに
                current_action = "turn_right"
                last_speed = target_speed
        elif char_key == 'q': # 左斜め前進
            if current_action != "diagonal_left_forward":
                print(f"左斜め前進 (目標速度: {target_speed})")
                motor.changing_Lforward(last_speed, target_speed) # 左斜め前進も滑らかに
                current_action = "diagonal_left_forward"
                last_speed = target_speed
        elif char_key == 'e': # 右斜め前進
            if current_action != "diagonal_right_forward":
                print(f"右斜め前進 (目標速度: {target_speed})")
                motor.changing_Rforward(last_speed, target_speed) # 右斜め前進も滑らかに
                current_action = "diagonal_right_forward"
                last_speed = target_speed
        elif char_key == 'u': # 速度アップ
            if target_speed < 100:
                target_speed += 10
                print(f"目標速度アップ: {target_speed}")
                # 現在の動作を継続するために、再度滑らかな変化を開始
                # ただし、現在の速度 (last_speed) から新しい目標速度 (target_speed) へ変化させる
                if current_action == "forward": motor.changing_forward(last_speed, target_speed)
                elif current_action == "backward": motor.changing_retreat(last_speed, target_speed)
                elif current_action == "turn_left": motor.changing_left(last_speed, target_speed)
                elif current_action == "turn_right": motor.changing_right(last_speed, target_speed)
                elif current_action == "diagonal_left_forward": motor.changing_Lforward(last_speed, target_speed)
                elif current_action == "diagonal_right_forward": motor.changing_Rforward(last_speed, target_speed)
                last_speed = target_speed # 新しい現在の速度を記録

        elif char_key == 'j': # 速度ダウン
            if target_speed > 0:
                target_speed -= 10
                print(f"目標速度ダウン: {target_speed}")
                if current_action == "forward": motor.changing_forward(last_speed, target_speed)
                elif current_action == "backward": motor.changing_retreat(last_speed, target_speed)
                elif current_action == "turn_left": motor.changing_left(last_speed, target_speed)
                elif current_action == "turn_right": motor.changing_right(last_speed, target_speed)
                elif current_action == "diagonal_left_forward": motor.changing_Lforward(last_speed, target_speed)
                elif current_action == "diagonal_right_forward": motor.changing_Rforward(last_speed, target_speed)
                last_speed = target_speed # 新しい現在の速度を記録

                if target_speed == 0: # 速度が0になったら完全に停止
                    print("速度0、停止します。")
                    motor.motor_stop_free()
                    current_action = "stop"
                    last_speed = 0 # 停止したので現在の速度も0

    except AttributeError:
        # 特殊キー (e.g., Space, Esc) の処理
        if key == keyboard.Key.space:
            if current_action != "stop":
                print("停止 (スペースキー)")
                motor.motor_stop_free()
                current_action = "stop"
                last_speed = 0 # 停止したので現在の速度も0
        elif key == keyboard.Key.esc:
            print("プログラム終了 (Escキーが押されました)")
            exit_event.set() # 終了イベントをセットして全てのスレッドに通知
            return False # リスナーを停止

def on_release(key):
    global current_action, last_speed, motor
    # 速度調整キー ('u', 'j') 以外が離されたら停止
    # ESCキーが押されて終了処理中の場合は何もしない
    # changing_xxx関数使用中はキーリリースで停止させない
    if not exit_event.is_set() and key not in [keyboard.KeyCode(char='u'), keyboard.KeyCode(char='j')]:
        # 現在の動作が「停止」以外で、かつ、変化中の動作でない場合のみ停止
        if current_action != "stop" and \
           not (current_action.startswith("changing_") or current_action.startswith("quick_")):
            print("キーを離したので停止")
            motor.motor_stop_free()
            current_action = "stop"
            last_speed = 0

# --- メイン処理 ---
if __name__ == "__main__":
    GPIO.setwarnings(False) # GPIOの警告を無効にする (開始時に設定)
    print("アプリケーションを開始します...")

    # 1. MotorDriverの初期化
    try:
        motor = MotorDriver(PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY)
        print("MotorDriverを初期化しました。")
    except Exception as e:
        print(f"エラー: MotorDriverの初期化中にエラーが発生しました: {e}")
        # GPIO.cleanup()は最後にまとめて行う
        exit(1)

    # 2. GPSデータ読み取りスレッドを開始
    gps_reader_thread_obj = threading.Thread(target=gps_reader_thread, daemon=True)
    gps_reader_thread_obj.start()

    # スレッドの起動を少し待つ（エラーチェックのため）
    time.sleep(2)
    if exit_event.is_set(): # GPSスレッドが起動直後にエラーで終了した場合
        print("GPSデータ読み取りスレッドの起動に失敗したため、プログラムを終了します。")
        if motor:
            motor.cleanup()
        GPIO.cleanup() # ここでGPIOクリーンアップ
        exit(1)

    print("\n---------------------------------------------------")
    print("ローバー制御開始。")
    print("操作キー:")
    print("  'w' : 前進 (滑らかに加速)")
    print("  's' : 後退 (滑らかに加速)")
    print("  'a' : 左旋回 (滑らかに加速)")
    print("  'd' : 右旋回 (滑らかに加速)")
    print("  'q' : 左斜め前進 (滑らかに加速)")
    print("  'e' : 右斜め前進 (滑らかに加速)")
    print("  'u' : 速度アップ (現在の目標速度を10増加)")
    print("  'j' : 速度ダウン (現在の目標速度を10減少)")
    print("  'Space' : 停止")
    print("  'Esc' : 全プログラム終了")
    print("---------------------------------------------------\n")

    # 3. キーボードリスナーを開始 (メインスレッドで実行)
    listener = None
    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join() # キーボードリスナーが終了するまで待機
    except Exception as e:
        print(f"メインスレッド(キーボードリスナー)でエラーが発生しました: {e}")
    finally:
        # プログラム終了処理
        print("メイン処理を終了します。全リソースをクリーンアップ中...")
        exit_event.set() # 全スレッドに終了を再度通知

        # GPSスレッドが終了するのを待つ（必要であればタイムアウトを設定）
        gps_reader_thread_obj.join(timeout=5) # 最大5秒待つ

        if motor:
            motor.cleanup() # MotorDriverのPWMを停止
            print("MotorDriverをクリーンアップしました。")
        
        # RPi.GPIOのクリーンアップは、最後に一度行われるのが理想
        try:
            GPIO.cleanup()
            print("RPi.GPIOをクリーンアップしました。")
        except Exception as e:
            print(f"RPi.GPIOのクリーンアップ中にエラーが発生しました: {e}")
            
        print("アプリケーションが完全に終了しました。")
