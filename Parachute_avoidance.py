import time
from motor import MotorDriver
import numpy as np
import cv2
from picamera2 import Picamera2
import math

# カメラ初期化
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ カメラが開けません")
    GPIO.cleanup()
    exit()

#


try:
    while True:
        ret, frame = cap.read()                            #ret:フレームが正常に読み込めたかどうかのtrue/false ,frame:実際の画像データ　を取得する。
        if not ret:                                        #retがfalseつまりフレームが読み込めていないとき
            print("⚠️ 画像取得に失敗")
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)       #hsv空間に変換

        # 赤色の範囲定義
        lower_red1 = np.array([0, 40, 50])                 #(Hue, Saturation, Value) 左から順に色相、彩度、明度
        upper_red1 = np.array([6, 255, 255])               
        lower_red2 = np.array([165, 40, 50])               
        upper_red2 = np.array([179, 255, 255])             

        # 赤色マスク生成
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)   #mask1作成　間のhsvを全て満たすもの
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)   #mask2作成　間のhsvを全て満たすもの
        mask = cv2.bitwise_or(mask1, mask2)                #mask=mask1+mask2

        # 赤色領域の輪郭抽出と面積計算
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_area = sum(cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 100)
        image_area = frame.shape[0] * frame.shape[1]
        percentage = (total_area / image_area) * 100

        
