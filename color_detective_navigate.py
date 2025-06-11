import cv2
import numpy as np
import time
from picamera2 import Picamera2
from motor import MotorDriver

#モータの初期化
driver = MotorDriver(
    PWMA=12, AIN1=23, AIN2=18,   # 左モーター用（モータA）
    PWMB=19, BIN1=16, BIN2=26,   # 右モーター用（モータB）
    STBY=21                      # STBYピン
)

# カメラ初期化と設定
picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (320, 240)})
picam2.configure(config)
picam2.start()
time.sleep(2)

#速度定義
Va = 0
Vb = 0

try:
    while True:
        # 画像取得
        frame = picam2.capture_array()

        frame = cv2.GaussianBlur(frame, (5, 5), 0)

        # BGR → HSV に変換
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 赤色の範囲指定
        lower_red1 = np.array([0, 30, 30])
        upper_red1 = np.array([20, 255, 255])
        lower_red2 = np.array([95, 30, 30])
        upper_red2 = np.array([130, 255, 255])

        # 赤マスク作成
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        # 面積計算
        red_area = np.count_nonzero(mask)
        total_area = frame.shape[0] * frame.shape[1]
        percentage = (red_area / total_area) * 100

        # 中心画素のh, s, v測定
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        center_pixel = hsv[hsv.shape[0]//2, hsv.shape[1]//2]
        print("中心のHSV値:", center_pixel)
        
        # 判定出力
        print(f"🔴 赤割合: {percentage:.2f}% → ", end="")
        if percentage >= 10.0:
             Vb = 0
             print("非常に近い（終了）")
             driver.changing_forward(Va, Vb)
             driver.motor_stop_brake()
             break
          
        elif percentage >= 5.0:
             Vb = 50
             print("近い")
             driver.changing_forward(Va, Vb)
             time.sleep(0.1)
             Va = Vb
          
        elif percentage >= 1.0:
             Vb = 100
             print("遠い")
             driver.changing_forward(Va, Vb)
             time.sleep(0.1)
             Va = Vb

        else: 
            print("範囲外")
            while True:
                driver.changing_forward(Va, 0)
                driver.changing_left(0, 15)
                driver.changing_left(15, 0)
                driver.motor_stop_brake()
               # 画像取得
                frame = picam2.capture_array()

                frame = cv2.GaussianBlur(frame, (5, 5), 0)

                # BGR → HSV に変換
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # 赤マスク作成
                mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                mask = cv2.bitwise_or(mask1, mask2)
    
                # 面積計算
                red_area = np.count_nonzero(mask)
                total_area = frame.shape[0] * frame.shape[1]
                percentage = (red_area / total_area) * 100

                if percentage >= 1.0:
                   Vb = 50
                   print("遠い")
                   driver.changing_forward(Va, Vb)
                   driver.motor_stop_brake()
                   Va = Vb
                   break               
                  
finally:
    picam2.close()
    print("カメラを閉じました。プログラム終了。")
