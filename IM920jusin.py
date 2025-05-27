import serial

PORT = 'COM4'  # 環境に合わせて変更
BAUDRATE = 19200

def receive_data():
    with serial.Serial(PORT, BAUDRATE, timeout=1) as ser:
        print("Listening for incoming messages...")
        while True:
            line = ser.readline().decode(errors='ignore').strip()
            if line:
                print(f"Received: {line}")

if __name__ == "__main__":
    receive_data()
