#goalyudo_nocamera.py→color_detective_navigate.py→このファイル
import math
import time
import RPi.GPIO as GPIO
from motor import MotorDriver

#コーン、ボールを一定割合以上検知し、静止している状態からのスタート
#ARLISSゴール付近のボールは大きさが既知であるため検知割合による距離の計算が可能

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
time.sleep(1)

#速度定義
Va = 0
Vb = 0

#関数定義(画像取得→画像処理→hsv変換→面積計算→割合計算)　戻り値はpercentage(画像赤色検知割合)
def get_percentage():
    frame = picam2.capture_array()
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 30, 30])
    upper_red1 = np.array([20, 255, 255])
    lower_red2 = np.array([95, 30, 30])
    upper_red2 = np.array([130, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    red_area = np.count_nonzero(mask)
    total_area = frame.shape[0] * frame.shape[1]
    percentage = (red_area / total_area) * 100
    return percentage

def get_block_number():
    
  
try:
    while true:
        driver.changing_left(0, 10)
        driver.changing_left(10, 0)
        percentage = take_a_picture()
        
        


