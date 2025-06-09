import RPi.GPIO as GPIO
import config
import math
import time
from micropyGPS import MicropyGPS

pi = math.pi
a = 6378245.0
ee = 0.00669342162296594323
x_pi = pi * 3000.0 / 180.0

class L76X:
    def __init__(self):
        self.gps = MicropyGPS(+8)
        self.config = config.config(9600)

        self.Lon = 0.0
        self.Lat = 0.0
        self.Status = 0
        self.Time_H = 0
        self.Time_M = 0
        self.Time_S = 0

        self.GPS_Lat = 0.0
        self.GPS_Lon = 0.0

        self.Lat_Google = 0.0
        self.Lon_Google = 0.0
        self.Lat_Baidu = 0.0
        self.Lon_Baidu = 0.0

    def send_command(self, command):
        check = ord(command[1])
        for c in command[2:]:
            check ^= ord(c)
        checksum = "*{:02X}".format(check)
        full_command = command + checksum + "\r\n"
        self.config.Uart_SendString(full_command.encode())
        print("Sent:", full_command.strip())

    def receive_gnrmc(self):
        sentence = ""
        while True:
            if self.gps.valid:
                self.Status = 1
            else:
                self.Status = 0

            byte = self.config.Uart_ReceiveByte()
            if byte == b'$':
                sentence = ''
                while byte != b'\r':
                    sentence += byte.decode()
                    self.gps.update(byte.decode())
                    byte = self.config.Uart_ReceiveByte()
                if '$GNRMC' in sentence:
                    break

        self.Lat = self.gps.latitude[0] + self.gps.latitude[1] / 100.0
        self.Lon = self.gps.longitude[0] + self.gps.longitude[1] / 100.0
        if self.gps.latitude[2] != 'N':
            self.Lat *= -1
        if self.gps.longitude[2] != 'E':
            self.Lon *= -1

        self.Time_H, self.Time_M, self.Time_S = self.gps.timestamp
        print("NMEA:", sentence)

    def transform_lat(self, x, y):
        ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y**2 + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(y * pi) + 40.0 * math.sin(y / 3.0 * pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(y / 12.0 * pi) + 320 * math.sin(y * pi / 30.0)) * 2.0 / 3.0
        return ret

    def transform_lon(self, x, y):
        ret = 300.0 + x + 2.0 * y + 0.1 * x**2 + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(x * pi) + 40.0 * math.sin(x / 3.0 * pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(x / 12.0 * pi) + 300.0 * math.sin(x / 30.0 * pi)) * 2.0 / 3.0
        return ret

    def transform(self):
        dLat = self.transform_lat(self.GPS_Lon - 105.0, self.GPS_Lat - 35.0)
        dLon = self.transform_lon(self.GPS_Lon - 105.0, self.GPS_Lat - 35.0)
        radLat = self.GPS_Lat / 180.0 * pi
        magic = math.sin(radLat)
        magic = 1 - ee * magic**2
        sqrtMagic = math.sqrt(magic)
        dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * pi)
        dLon = (dLon * 180.0) / (a / sqrtMagic * math.cos(radLat) * pi)
        self.Lat_Google = self.GPS_Lat + dLat
        self.Lon_Google = self.GPS_Lon + dLon

    def bd_encrypt(self):
        x = self.Lon_Google
        y = self.Lat_Google
        z = math.sqrt(x**2 + y**2) + 0.00002 * math.sin(y * x_pi)
        theta = math.atan2(y, x) + 0.000003 * math.cos(x * x_pi)
        self.Lon_Baidu = z * math.cos(theta) + 0.0065
        self.Lat_Baidu = z * math.sin(theta) + 0.006

    def calculate_google_coordinates(self, lat, lon):
        self.GPS_Lat = lat % 1 * 100 / 60 + math.floor(lat)
        self.GPS_Lon = lon % 1 * 100 / 60 + math.floor(lon)
        self.transform()

    def calculate_baidu_coordinates(self, lat, lon):
        self.calculate_google_coordinates(lat, lon)
        self.bd_encrypt()

    def set_baudrate(self, baudrate):
        self.config.Uart_Set_Baudrate(baudrate)

    def exit_backup_mode(self):
        GPIO.setup(self.config.FORCE, GPIO.OUT)
        time.sleep(1)
        GPIO.output(self.config.FORCE, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(self.config.FORCE, GPIO.LOW)
        time.sleep(1)
        GPIO.setup(self.config.FORCE, GPIO.IN)
