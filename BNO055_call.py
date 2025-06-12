import smbus
import time
import struct
from BNO055 import BNO055

#インスタンス作成
bno = BNO055()
time.sleep(1)
bno.setExternalCrystalUse(True)      #外部水晶振動子使用(クロック)
setMode(BNO055.OPERATION_MODE_NDOF)  #NDOFモードに設定
for i in range(20):
    print(bno.getVector(BNO055.VECTOR_EULER))
    time.sleep(0.1)
