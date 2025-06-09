# run_motor.py
import time
from motor import MotorDriver

if __name__ == "__main__":
    # ① MotorDriver のインスタンスを作成（__init__ は自動で呼ばれる）
    driver = MotorDriver(
        PWMA=12, AIN1=23, AIN2=18,
        PWMB=19, BIN1=16, BIN2=26,
        STBY=21,
        freq=1000
    )

    # ② メソッドはインスタンス経由で呼び出す
    print("前進加速中")
    driver.changing_forward(0, 80)

    print("前進減速中")
    driver.changing_forward(80, 0)

    print("右折加速中")
    driver.changing_right(0, 50)

    print("右折減速中")
    driver.changing_right(50, 0)

    # ③ 最後に GPIO をクリーンアップ
    driver.cleanup()
  
