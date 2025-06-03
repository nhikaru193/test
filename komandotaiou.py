ser.write(b'VER\r\n')
time.sleep(0.5)
print(ser.read_all())
