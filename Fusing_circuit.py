# coding: utf-8
import RPi.GPIO as GPIO
import time

# GPIOのピン番号設定
# 回路図の「GPIO25」はBCMモードの25番ピンを指す
NICHROME_PIN = 25

# ニクロム線をオンにしておく時間（秒）
# !!! 注意: この値は非常に重要です。最初は0.5秒などの短い時間から試してください。
HEATING_DURATION_SECONDS = 2.0

# GPIOのモードをBCMに設定（GPIO番号で指定）
GPIO.setmode(GPIO.BCM)

# GPIO25を出力モードに設定し、初期状態をLOW(オフ)に設定
GPIO.setup(NICHROME_PIN, GPIO.OUT, initial=GPIO.LOW)

print("ニクロム線溶断シーケンスを開始します。")

# try...finally構文で、プログラムがエラーで中断しても必ずGPIOをクリーンアップする
try:
    # --- ニクロム線をオンにする ---
    print(f"GPIO{NICHROME_PIN} をHIGHに設定し、ニクロム線をオンにします。")
    GPIO.output(NICHROME_PIN, GPIO.HIGH)

    # --- 指定した時間だけ待機 ---
    print(f"{HEATING_DURATION_SECONDS}秒間、加熱します...")
    time.sleep(HEATING_DURATION_SECONDS)

    # --- ニクロム線をオフにする ---
    print(f"GPIO{NICHROME_PIN} をLOWに設定し、ニクロム線をオフにします。")
    GPIO.output(NICHROME_PIN, GPIO.LOW)
    
    print("シーケンスが正常に完了しました。")

except KeyboardInterrupt:
    # Ctrl+Cが押された場合に備えて、ここでもオフにする
    print("プログラムが中断されました。")
    GPIO.output(NICHROME_PIN, GPIO.LOW)

finally:
    # --- GPIOの設定をリセット ---
    # この処理をしないと、次回以降GPIOが正常に動作しない可能性がある
    GPIO.cleanup()
    print("GPIOのクリーンアップを実行しました。")
