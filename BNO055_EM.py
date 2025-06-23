import smbus
import time
import struct
from BNO055 import BNO055

bno = BNO055()
if bno.begin() is not True:
    print("Error initializing device")
    exit()
    time.sleep(1)
bno.setMode(BNO055.OPERATION_MODE_NDOF)
bno.setExternalCrystalUse(True)
time.sleep(1)
heading = bno.get_heading()
print(heading)
