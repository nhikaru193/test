import pigpio, time, pynmea2

TX_PIN = 17
RX_PIN = 27
BAUD = 9600

pi = pigpio.pi()
pi.bb_serial_read_open(RX_PIN, BAUD, 8)

buf = ""
try:
    while True:
        count, data = pi.bb_serial_read(RX_PIN)
        if count > 0:
            buf += data.decode("ascii", errors="ignore")
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            if line.startswith("$GP"):
                try:
                    msg = pynmea2.parse(line.strip())
                except pynmea2.ParseError:
                    continue
                if hasattr(msg, 'latitude') and hasattr(msg, 'longitude'):
                    print(f"緯度: {msg.latitude:.6f}, 経度: {msg.longitude:.6f}")
        time.sleep(0.005)

except KeyboardInterrupt:
    pass

finally:
    pi.bb_serial_read_close(RX_PIN)
    pi.stop()
