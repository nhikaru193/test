import time
import pigpio # <-- pigpioをインポート
import A_BNO055
import smbus
import struct

# RPi.GPIOは使わないので削除
# import RPi.GPIO as GPIO

class MotorDriver():
    # 初期設定関数の定義
    def __init__(self,
                 PWMA, AIN1, AIN2,
                 PWMB, BIN1, BIN2, STBY,
                 freq = 1000):
        
        # pigpioデーモンに接続
        self.pi = pi
        if not self.pi.connected:
            raise RuntimeError("pigpioデーモンに接続できません。sudo pigpiod を実行してください。")

        # GPIO初期設定 (pigpioではsetupは不要)
        self.pi.set_mode(AIN1, pigpio.OUTPUT)
        self.pi.set_mode(AIN2, pigpio.OUTPUT)
        self.pi.set_mode(PWMA, pigpio.OUTPUT)
        self.pi.set_mode(BIN1, pigpio.OUTPUT)
        self.pi.set_mode(BIN2, pigpio.OUTPUT)
        self.pi.set_mode(PWMB, pigpio.OUTPUT)
        self.pi.set_mode(STBY, pigpio.OUTPUT)
        
        # モータ起動 (STBYピンをHIGHにしてモータードライバを有効化)
        self.pi.write(STBY, 1)

        # self型の関数に格納
        self.A1, self.A2 = AIN1, AIN2
        self.B1, self.B2 = BIN1, BIN2
        self.pwma = PWMA # PWMピン番号を格納
        self.pwmb = PWMB # PWMピン番号を格納
        
        # pigpioでPWM周波数を設定
        self.pi.set_PWM_frequency(self.pwma, freq)
        self.pi.set_PWM_frequency(self.pwmb, freq)
        
        # motorの起動：デューティ比0⇒停止
        self.pi.set_PWM_dutycycle(self.pwma, 0)
        self.pi.set_PWM_dutycycle(self.pwmb, 0)

    # 右回頭
    def motor_right(self, speed):
        self.pi.write(self.A1, 0)  # 左モーター後退 (HIGH:前進, LOW:後退)
        self.pi.write(self.A2, 1)
        self.pi.write(self.B1, 0)  # 右モーター後退
        self.pi.write(self.B2, 1)
        self.pi.set_PWM_dutycycle(self.pwma, int(speed * 2.55)) # デューティ比を0-255に変換
        self.pi.set_PWM_dutycycle(self.pwmb, int(speed * 2.55))

    # 左回頭
    def motor_left(self, speed):
        self.pi.write(self.A1, 1) # 左モーター前進
        self.pi.write(self.A2, 0)
        self.pi.write(self.B1, 1) # 右モーター前進
        self.pi.write(self.B2, 0)
        self.pi.set_PWM_dutycycle(self.pwma, int(speed * 2.55))
        self.pi.set_PWM_dutycycle(self.pwmb, int(speed * 2.55))

    # 後退
    def motor_retreat(self, speed):
        self.pi.write(self.A1, 1)
        self.pi.write(self.A2, 0)
        self.pi.write(self.B1, 0)
        self.pi.write(self.B2, 1)
        self.pi.set_PWM_dutycycle(self.pwma, int(speed * 2.55))
        self.pi.set_PWM_dutycycle(self.pwmb, int(speed * 2.55))
    
    # モータのトルクでブレーキをかける
    def motor_stop_free(self):
        self.pi.set_PWM_dutycycle(self.pwma, 0)
        self.pi.set_PWM_dutycycle(self.pwmb, 0)
        self.pi.write(self.A1, 0)
        self.pi.write(self.A2, 0)
        self.pi.write(self.B1, 0)
        self.pi.write(self.B2, 0)
    
    # ガチブレーキ
    def motor_stop_brake(self):
        self.pi.set_PWM_dutycycle(self.pwma, 0)
        self.pi.set_PWM_dutycycle(self.pwmb, 0)
        self.pi.write(self.A1, 1)
        self.pi.write(self.A2, 1)
        self.pi.write(self.B1, 1)
        self.pi.write(self.B2, 1)

    # リソース解放
    def cleanup(self):
        self.pi.set_PWM_dutycycle(self.pwma, 0)
        self.pi.set_PWM_dutycycle(self.pwmb, 0)
        self.pi.stop()
    
    # 前進：任意
    def motor_forward(self, speed):
        self.pi.write(self.A1, 0)
        self.pi.write(self.A2, 1)
        self.pi.write(self.B1, 1)
        self.pi.write(self.B2, 0)
        self.pi.set_PWM_dutycycle(self.pwma, int(speed * 2.55))
        self.pi.set_PWM_dutycycle(self.pwmb, int(speed * 2.55))
    
    def motor_Lforward(self, speed):
        self.pi.write(self.A1, 0)
        self.pi.write(self.A2, 1)
        self.pi.set_PWM_dutycycle(self.pwma, int(speed * 2.55))
            
    def motor_Rforward(self, speed):
        self.pi.write(self.B1, 1)
        self.pi.write(self.B2, 0)
        self.pi.set_PWM_dutycycle(self.pwmb, int(speed * 2.55))
            
    # 前進：回転数制御
    def changing_forward(self, before, after):
        # ... (内部の処理は同様)
        # ただし、self.motor_forward(speed) は修正後の関数を使う
        for i in range(1, 100):
            delta_speed = (after - before) / 100
            speed = before + i * delta_speed
            self.motor_forward(speed)
            time.sleep(0.02)
    
    # 右折：回転数制御
    def changing_right(self, before, after):
        for i in range(50):
            delta_speed = (after - before) / 50
            speed = before + i * delta_speed
            self.motor_right(speed)
            time.sleep(0.03)
    
    # 左折（同様）
    def changing_left(self, before, after):
        for i in range(50):
            delta_speed = (after - before) / 50
            speed = before + i * delta_speed
            self.motor_left(speed)
            time.sleep(0.03)
    
    # 後退：回転数制御
    def changing_retreat(self, before, after):
        for i in range(50):
            delta_speed = (after - before) / 50
            speed = before + i * delta_speed
            self.motor_retreat(speed)
            time.sleep(0.03)

    def quick_right(self, before, after):
        for i in range(10):
            delta_speed = (after - before) / 10
            speed = before + i * delta_speed
            self.motor_right(speed)
            time.sleep(0.02)
    
    def quick_left(self, before, after):
        for i in range(10):
            delta_speed = (after - before) / 10
            speed = before + i * delta_speed
            self.motor_left(speed)
            time.sleep(0.02)
    
    def changing_moving_forward(self, Lmotor_b, Lmotor_a ,Rmotor_b, Rmotor_a):
        for i in range(1, 20):
            delta_speed_L = (Lmotor_a - Lmotor_b) / 20
            delta_speed_R = (Rmotor_a - Rmotor_b) / 20
            speed_L = Lmotor_b + i * delta_speed_L
            speed_R = Rmotor_b + i * delta_speed_R
            self.motor_Lforward(speed_L)
            self.motor_Rforward(speed_R)
            time.sleep(0.02)
    
    def petit_forward(self, before, after):
        for i in range (1, 5):
            delta_speed = (after - before) / 5
            speed = before + i * delta_speed
            self.motor_forward(speed)
            time.sleep(0.02)

    def petit_left(self, before, after):
        for i in range (1, 5):
            delta_speed = (after - before) / 5
            speed = before + i * delta_speed
            self.motor_left(speed)
            time.sleep(0.02)

    def petit_right(self, before, after):
        for i in range (1, 5):
            delta_speed = (after - before) / 5
            speed = before + i * delta_speed
            self.motor_right(speed)
            time.sleep(0.02)
            
    def petit_petit(self, count):
        for i in range (1, count):
            self.petit_forward(0, 90)
            self.petit_forward(90, 0)
            time.sleep(0.2)

    def petit_petit_retreat(self, count):
        for i in range (1, count):
            self.petit_back(0, 90)
            self.petit_back(90, 0)
            time.sleep(0.2)
