
#import RPi.GPIO as GPIO
import pigpio
import time

#------------------------#
def install(duty=12.5, duration=2.5):
    pi = pigpio.pi()
    if not pi.connected:
        print("pigpiodデーモンに接続できません。sudo pigpiodを実行してください。")
        return

    SERVO_PIN = 13
    try:
        print("物資を格納するため、サーボモータの起動を行います")
        # RPi.GPIOのGPIO.setmode, GPIO.setupは不要
        
        # pigpioでサーボのパルス幅を設定 (デューティ比からパルス幅に変換)
        # 50Hzの場合、2.5%が500us, 12.5%が2500us
        pulse_width = int((duty / 100) * 20000)
        
        print(f"物資をデューティ比{duty} (パルス幅{pulse_width}us)、格納時間{duration}で設置します")
        pi.set_servo_pulsewidth(SERVO_PIN, pulse_width)
        time.sleep(duration + 0.5) # サーボが動く時間+安定時間

    except KeyboardInterrupt:
        print("プログラムの中断が行われました")

    finally:
        pi.set_servo_pulsewidth(SERVO_PIN, 0) # パルス幅を0にして停止
        pi.stop()
        print("物資の格納が正常に終了しました")
        time.sleep(2)
#------------------------#

#------------------------#
def release(duty=2.5, duration=6):
    pi = pigpio.pi()
    if not pi.connected:
        print("pigpiodデーモンに接続できません。sudo pigpiodを実行してください。")
        return
        
    SERVO_PIN = 13
    try:
        print("物資を設置するため、サーボモータの起動を行います")
        # RPi.GPIOのGPIO.setmode, GPIO.setupは不要

        # pigpioでサーボのパルス幅を設定
        pulse_width = int((duty / 100) * 20000)
        
        print(f"物資をデューティ比{duty} (パルス幅{pulse_width}us)、設置時間{duration}で設置します")
        pi.set_servo_pulsewidth(SERVO_PIN, pulse_width)
        time.sleep(duration + 0.5) # サーボが動く時間+安定時間
        
    except KeyboardInterrupt:
        print("プログラムの中断が行われました")

    finally:
        pi.set_servo_pulsewidth(SERVO_PIN, 0) # パルス幅を0にして停止
        pi.stop()
        print("物資の設置が正常に終了しました")
        time.sleep(2)
#------------------------#
