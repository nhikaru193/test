import smbus
import time
import struct
from BNO055 import BNO055

#インスタンス作成
bno = BNO055()
bno.begin()
time.sleep(1)
bno.setExternalCrystalUse(True)      #外部水晶振動子使用(クロック)
bno.setMode(BNO055.OPERATION_MODE_NDOF)  #NDOFモードに設定

#校正
print("キャリブレーション中... センサをいろんな向きにゆっくり回してください")
while True:
    sys, gyro, accel, mag = bno.getCalibration()
    print(f"Calib → Sys:{sys}, Gyro:{gyro}, Acc:{accel}, Mag:{mag}", end='\r')
    if gyro == 3 and mag == 3:
#姿勢
        time.sleep(1)
        for i in range(20):
            print(bno.getVector(BNO055.VECTOR_EULER))
            print(bno.getVector(BNO055.VECTOR_EULER)[0])
            time.sleep(0.1)

#
        time.sleep(1)
        for i in range(20):
            print(bno.getVector(BNO055.VECTOR_GRAVITY))
            time.sleep(0.1)

#
        time.sleep(1)
        for i in range(20):
            print(bno.getVector(BNO055.VECTOR_GYROSCOPE))
            time.sleep(0.1)
