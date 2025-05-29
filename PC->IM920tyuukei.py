import serial
import time
import sys

# ラズパイのUARTポート（/dev/serial0）
pi_uart = serial.Serial('/dev/serial0', 19200, timeout=0.1)

# PCとの接続があるなら、stdin/stdoutで代用する（Tera Termからの入力を想定）
print("IM920SL中継ブリッジ 起動中")

try:
    while True:
        # PC側からの入力をIM920SLへ
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            if line:
                pi_uart.write(line.encode('utf-8'))

        # IM920SLからの受信をPC側に表示
        if pi_uart.in_waiting:
            data = pi_uart.readline().decode('utf-8', errors='ignore').strip()
            if data:
                print(data)

except KeyboardInterrupt:
    pi_uart.close()
    print("終了しました")
