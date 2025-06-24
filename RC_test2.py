import RPi.GPIO as GPIO
import time
import socket
from pynput import keyboard
import threading
import serial
import pigpio

# motor.py から MotorDriver クラスをインポート
# motor.py は前回の変更後のMotorDriverクラスを持つものとします。
from motor import MotorDriver

# --- グローバル変数と初期設定 ---
# モーター制御ピン (ご自身の配線に合わせて変更してください)
PWMA = 12
AIN1 = 23
AIN2 = 18

PWMB = 19
BIN1 = 16
BIN2 = 26

STBY = 21

# GPS (ソフトUART) 用のピンとボーレート
GPS_RX_PIN = 17
GPS_BAUD = 9600

# グローバルなインスタンスと状態変数
motor = None
pi = None # pigpioインスタンス
current_direction = "stop" # 現在の進行方向 (forward, backward, turn_left, turn_right, diagonal_left_forward, diagonal_right_forward, stop)
# 速度制御用の変数
actual_speed = 0  # 現在の実際のモーターデューティ比 (0-100)
target_speed = 50 # 目標とするモーターデューティ比 (0-100)
speed_step = 2    # 一度の更新で速度が変化する量（例: 2%ずつ変化）
speed_update_interval = 0.05 # 速度を更新する間隔（秒）

# スレッド終了のためのイベント
exit_event = threading.Event()
# 速度更新スレッドの停止を制御するイベント (今回は未使用だが、今後の拡張のために残しておく)
speed_update_event = threading.Event()

# --- GPSデータ処理関数 ---
def convert_to_decimal(coord, direction):
    degrees = int(coord[:2]) if direction in ['N', 'S'] else int(coord[:3])
    minutes = float(coord[2:]) if direction in ['N', 'S'] else float(coord[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

# --- GPSデータ読み取りを担当するスレッド関数 ---
def gps_reader_thread():
    global pi

    print("GPSデータ読み取りスレッドを開始します...")

    pi = pigpio.pi()
    if not pi.connected:
        print("エラー: pigpio デーモンに接続できません。pigpiodが実行されているか確認してください。")
        exit_event.set()
        return

    err = pi.bb_serial_read_open(GPS_RX_PIN, GPS_BAUD, 8)
    if err != 0:
        print(f"エラー: ソフトUART RX の設定に失敗：GPIO={GPS_RX_PIN}, {GPS_BAUD}bps, エラーコード: {err}")
        exit_event.set()
        pi.stop()
        return

    print(f"▶ ソフトUART RX を開始：GPIO={GPS_RX_PIN}, {GPS_BAUD}bps")

    try:
        while not exit_event.is_set():
            (count, data) = pi.bb_serial_read(GPS_RX_PIN)
            if count and data:
                try:
                    text = data.decode("ascii", errors="ignore")
                    if "$GNRMC" in text:
                        lines = text.split("\n")
                        for line in lines:
                            if "$GNRMC" in line:
                                parts = line.strip().split(",")
                                if len(parts) > 6 and parts[2] == "A":
                                    try:
                                        lat = convert_to_decimal(parts[3], parts[4])
                                        lon = convert_to_decimal(parts[5], parts[6])
                                        # print(f"GPSデータ受信: 緯度={lat:.6f}, 経度={lon:.6f}") # 頻繁に出力するとログが流れるためコメントアウト
                                    except ValueError as ve:
                                        print(f"GPS座標の変換エラー: {ve}, ライン: {line.strip()}")
                                elif len(parts) <= 6:
                                    pass # print(f"GPSデータフォーマットエラー (長さ不足): {line.strip()}")
                except UnicodeDecodeError as ude:
                    print(f"GPSデータデコードエラー: {ude}, データ: {data}")
                except Exception as e:
                    print(f"GPSデータ処理中に予期せぬエラー: {e}")
            time.sleep(0.1)

    except Exception as e:
        print(f"GPSデータ読み取りスレッドでエラーが発生しました: {e}")
    finally:
        print("GPSデータ読み取りスレッドを終了します。クリーンアップ中...")
        if pi and pi.connected:
            pi.bb_serial_read_close(GPS_RX_PIN)
            pi.stop()
            print("pigpioリソースをクリーンアップしました。")

# --- モーター速度調整スレッド ---
def motor_speed_control_thread():
    global actual_speed, target_speed, current_direction, motor, speed_step, speed_update_interval

    print("モーター速度制御スレッドを開始します...")
    last_action = "INITIAL_STATE" # 前回の動作を記憶するための初期値

    while not exit_event.is_set():
        # 目標速度と現在の速度が異なる場合、滑らかに調整
        if actual_speed < target_speed:
            actual_speed = min(actual_speed + speed_step, target_speed)
        elif actual_speed > target_speed:
            actual_speed = max(actual_speed - speed_step, target_speed)

        # 実際のモーター制御コマンドを送信
        # current_direction が変更された場合、または速度調整が必要な場合にのみコマンドを送信
        if current_direction == "forward":
            motor.motor_forward(actual_speed)
        elif current_direction == "backward":
            motor.motor_retreat(actual_speed)
        elif current_direction == "turn_left":
            motor.motor_left(actual_speed)
        elif current_direction == "turn_right":
            motor.motor_right(actual_speed)
        elif current_direction == "diagonal_left_forward":
            motor.motor_Lforward(actual_speed)
        elif current_direction == "diagonal_right_forward":
            motor.motor_Rforward(actual_speed)
        elif current_direction == "stop":
            # 停止状態の場合は実際の速度を0に保つ
            if actual_speed != 0: # actual_speed が0でない場合のみ停止処理
                actual_speed = 0
                motor.motor_stop_free()
            else:
                # 既に停止状態であれば、再度コマンドを送る必要はない
                pass 
        
        # 動作が変わった場合、または速度が目標に達していない場合にログに出力
        # ログを頻繁に出しすぎないように調整
        if current_direction != last_action:
            print(f"現在の動作: {current_direction}, 目標速度: {target_speed}, 実際の速度: {actual_speed}")
            last_action = current_direction
        
        # 速度調整中のみ進捗を出力 (現在の動作が停止以外で、かつ actual_speed が target_speed と異なる場合)
        if current_direction != "stop" and actual_speed != target_speed:
             print(f"速度調整中: 現在の速度={actual_speed:.0f}, 目標速度={target_speed}")


        time.sleep(speed_update_interval) # 定期的に更新

    print("モーター速度制御スレッドを終了します。")


# --- キーボード入力処理 ---
def on_press(key):
    global current_direction, target_speed, actual_speed

    if exit_event.is_set():
        return False # 終了イベントがセットされていたらリスナーを停止

    try:
        char_key = getattr(key, 'char', None)

        # 方向キーが押された場合の処理
        # ここで重要なのは、停止状態から動き出す際に actual_speed を0から開始させることです。
        # target_speed はそのままで、motor_speed_control_thread が実際の加速を処理します。
        if char_key == 'w':
            if current_direction != "forward":
                print("コマンド: 前進")
                # 停止状態から動き出す場合、実際の速度を0にリセットしてスムーズな加速を促す
                if current_direction == "stop":
                    actual_speed = 0
                current_direction = "forward"
        elif char_key == 's':
            if current_direction != "backward":
                print("コマンド: 後退")
                if current_direction == "stop":
                    actual_speed = 0
                current_direction = "backward"
        elif char_key == 'a':
            if current_direction != "turn_left":
                print("コマンド: 左旋回")
                if current_direction == "stop":
                    actual_speed = 0
                current_direction = "turn_left"
        elif char_key == 'd':
            if current_direction != "turn_right":
                print("コマンド: 右旋回")
                if current_direction == "stop":
                    actual_speed = 0
                current_direction = "turn_right"
        elif char_key == 'q':
            if current_direction != "diagonal_left_forward":
                print("コマンド: 左斜め前進")
                if current_direction == "stop":
                    actual_speed = 0
                current_direction = "diagonal_left_forward"
        elif char_key == 'e':
            if current_direction != "diagonal_right_forward":
                print("コマンド: 右斜め前進")
                if current_direction == "stop":
                    actual_speed = 0
                current_direction = "diagonal_right_forward"
        
        # 速度調整キーが押された場合の処理
        elif char_key == 'u': # 速度アップ
            if target_speed < 100:
                target_speed += 10
                print(f"目標速度アップ: {target_speed}")
        elif char_key == 'j': # 速度ダウン
            if target_speed > 0:
                target_speed -= 10
                print(f"目標速度ダウン: {target_speed}")
            if target_speed == 0:
                print("コマンド: 完全停止 (速度0)")
                current_direction = "stop" # 目標速度が0になったら停止状態に遷移

    except AttributeError:
        # 特殊キー (e.g., Space, Esc) の処理
        if key == keyboard.Key.space:
            if current_direction != "stop":
                print("コマンド: 停止 (スペースキー)")
                current_direction = "stop"
                target_speed = 0 # 停止なので目標速度も0
        elif key == keyboard.Key.esc:
            print("プログラム終了 (Escキーが押されました)")
            exit_event.set() # 全スレッドに終了を通知
            return False # リスナーを停止

def on_release(key):
    global current_direction

    if exit_event.is_set():
        return

    char_key = getattr(key, 'char', None)
    # 速度調整キー ('u', 'j') 以外が離されたら、現在の動作を停止
    # ただし、spaceキーやescキーが離された場合は、すでにon_pressで処理済みなので除外
    if char_key not in ['u', 'j'] and key not in [keyboard.Key.space, keyboard.Key.esc]:
        # すでに停止状態でない場合のみ停止コマンドを送信
        if current_direction != "stop":
            print("コマンド: キーを離したので停止")
            current_direction = "stop"
            # target_speed は変更しない (後で同じ速度で再開できるように)
            # actual_speed は motor_speed_control_thread が0にする

# --- メイン処理 ---
if __name__ == "__main__":
    GPIO.setwarnings(False)
    print("アプリケーションを開始します...")

    # 1. MotorDriverの初期化
    try:
        motor = MotorDriver(PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY)
        print("MotorDriverを初期化しました。")
    except Exception as e:
        print(f"エラー: MotorDriverの初期化中にエラーが発生しました: {e}")
        GPIO.cleanup()
        exit(1)

    # 2. GPSデータ読み取りスレッドを開始
    gps_reader_thread_obj = threading.Thread(target=gps_reader_thread, daemon=True)
    gps_reader_thread_obj.start()

    # 3. モーター速度制御スレッドを開始
    motor_controller_thread = threading.Thread(target=motor_speed_control_thread, daemon=True)
    motor_controller_thread.start()

    time.sleep(2) # スレッド起動を少し待つ
    if exit_event.is_set():
        print("スレッドの起動に失敗したため、プログラムを終了します。")
        if motor:
            motor.cleanup()
        GPIO.cleanup()
        exit(1)

    print("\n---------------------------------------------------")
    print("ローバー制御開始。")
    print("操作キー:")
    print("  'w' : 前進")
    print("  's' : 後退")
    print("  'a' : 左旋回")
    print("  'd' : 右旋回")
    print("  'q' : 左斜め前進")
    print("  'e' : 右斜め前進")
    print("  'u' : 速度アップ (目標速度を10増加)")
    print("  'j' : 速度ダウン (目標速度を10減少)")
    print("  'Space' : 停止")
    print("  'Esc' : 全プログラム終了")
    print("---------------------------------------------------\n")

    # 4. キーボードリスナーを開始 (メインスレッドで実行)
    listener = None
    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    except Exception as e:
        print(f"メインスレッド(キーボードリスナー)でエラーが発生しました: {e}")
    finally:
        print("メイン処理を終了します。全リソースをクリーンアップ中...")
        exit_event.set() # 全スレッドに終了を通知

        # スレッドが終了するのを待つ
        gps_reader_thread_obj.join(timeout=5)
        motor_controller_thread.join(timeout=5)

        if motor:
            motor.cleanup()
            print("MotorDriverをクリーンアップしました。")
        
        try:
            GPIO.cleanup()
            print("RPi.GPIOをクリーンアップしました。")
        except Exception as e:
            print(f"RPi.GPIOのクリーンアップ中にエラーが発生しました: {e}")
            
        print("アプリケーションが完全に終了しました。")
