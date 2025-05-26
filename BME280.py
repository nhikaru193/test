import smbus

##############データシートを見ながら読むように！！！！！！！！#################

#補正用
t_fine = 0.0

digT = []
digP = []
digH = []

#I2C設定
i2c = smbus.SMBus(1)
address = 0x76                                        #5番端子をgndであるので、0x76

#BME280の設定
def init_bme280():
    ret = i2c.write_byte_data(address, 0xF2, 0x01)    #ctrl_hum, オーバーサンプリング0x01(1)回
    ret = i2c.write_byte_data(address, 0xF4, 0x27)    #ctrl_meas, 0x27は2進数で00100111, 001→温度1回測定, 001→気圧1回測定, 11→通常モード
    ret = i2c.write_byte_data(address, 0xF5, 0xA0)    #config, 0xA0は二進数で10100000, 101→t_sb;スタンバイ時間1000 ms, 000→フィルターオフ, 00→spiインターフェイスオフ, データシート要参照

#補正データ読み込み
def read_compensate():
    #温度補正データ読み込み
    dat_t = i2c.read_i2c_block_data(address, 0x88, 0x6) #0x88(calibデータレジスタ)から0x6つまり6バイト(1byteは8bit)読み出し,　行列形式(A, B, C, D, E, F)

    #digTは温度補正係数リストとして作成
    digT.append((dat_t[1] << 8) | dat_t[0])             #先ほどのdat_t行列の0番目と1番目の要素を合体, dat_t[1]に0を8個後ろから付け足し、dat_t[0]と足し合わせる
    digT.append((dat_t[3] << 8) | dat_t[2])             #同様
    digT.append((dat_t[5] << 8) | dat_t[4])             #同様
    
    #極性判断(2の15乗;15bitが絶対値部分, のこりの1bitで符号判定;0→-、1→＋)
    for i in range(1, 2):                               
        if digT[i] >= 32768:
            digT[i] -= 65536
    
    #気圧補正データ読み込み
    dat_p = i2c.read_i2c_block_data(address, 0x8E, 0x12)   #0x8E(Pressure_calibデータレジスタ)から0x6つまり6バイト(1byteは8bit)読み出し,　行列形式(A, B, C, D)
    
    digP.append((dat_p[1] << 8) | dat_p[0])                #同様
    digP.append((dat_p[3] << 8) | dat_p[2])                 
    digP.append((dat_p[5] << 8) | dat_p[4])
    digP.append((dat_p[7] << 8) | dat_p[6])
    digP.append((dat_p[9] << 8) | dat_p[8])
    digP.append((dat_p[11] << 8) | dat_p[10])
    digP.append((dat_p[13] << 8) | dat_p[12])
    digP.append((dat_p[15] << 8) | dat_p[14])
    digP.append((dat_p[17] << 8) | dat_p[16])
    
    #極性判断(さっきと同じ)
    for i in range(1, 8):
        if digP[i] >= 32768:
            digP[i] -= 65536
    
    #湿度補正データ読み込み
    dh = i2c.read_byte_data(address, 0xA1)                     #0xA1つまり温度補正係数8bit読み込み
    digH.append(dh)
    dat_h = i2c.read_i2c_block_data(address, 0xE1, 0x08)       #0xE1(Humidity_calibデータレジスタ)から0x8つまり8バイト(1byteは8bit)読み出し,　行列形式(A, B, C, D, E, F, G, H)
    digH.append((dat_h[1] << 8) | dat_h[0])                    #同様
    digH.append(dat_h[2])
    digH.append((dat_h[3] << 4) | (0x0F & dat_h[4]))
    digH.append((dat_h[5] << 4) | ((dat_h[4] >> 4) & 0x0F))
    digH.append(dat_h[6])
    
    #極性判断
    if digH[1] >= 32768:
        digH[1] -= 65536
    
    for i in range(3, 4):
        if digH[i] >= 32768:
            digH[i] -= 65536
    
    if digH[5] >= 128:
            digH[5] -= 256

#測定データ読み込み
def read_data():
    
    #データ読み込み
    dat = i2c.read_i2c_block_data(address, 0xF7, 0x08)          #0xF7から8byte分の読みだし、データシートP25参照、8byte分→press_msbからhum_lsbの8つ分なのですべてのデータの読み出しができる
    
    #データ変換
    dat_p = (dat[0] << 16 | dat[1] << 8 | dat[2]) >> 4
    dat_t = (dat[3] << 16 | dat[4] << 8 | dat[5]) >> 4
    dat_h = dat[6] << 8 | dat[7]
    
    #補正
    tmp = bme280_compensate_t(dat_t)
    prs = bme280_compensate_p(dat_p)
    hum = bme280_compensate_h(dat_h)
    
    #表示
    print('t = ' + str(tmp))
    print('p = ' + str(prs))
    print('h = ' + str(hum))

#温度補正
def bme280_compensate_t(adc_T):
    
    global t_fine
    
    var1 = (adc_T / 8.0 - digT[0] * 2.0) * (digT[1]) / 2048.0
    var2 = (adc_T / 16.0 - digT[0]) * (adc_T / 16.0 - digT[0]) / 4096.0 \
            * digT[2] / 16384.0 
    
    t_fine = var1 + var2
    
    t = (t_fine * 5 + 128) / 256
    t= t / 100
    
    return t

#湿度補正
def bme280_compensate_p(adc_P):
    
    global  t_fine
    p = 0.0
    
    var1 = t_fine - 128000.0
    var2 = var1 * var1 * digP[5]
    var2 = var2 + ((var1 * digP[4]) * 131072.0)
    var2 = var2 + (digP[3] * 3.435973837e10)    
    var1 = ((var1 * var1 * digP[2])/ 256.0) + (var1 * digP[1]) * 4096
    var1 = (1.407374884e14 + var1) * (digP[0] / 8589934592.0)
    
    if var1 == 0:
        return 0
    
    p = 1048576.0 - adc_P
    p = ((p * 2147483648.0 - var2) * 3125) / var1
    
    var1 = (digP[8] * (p / 8192.0) * (p / 8192.0)) / 33554432.0
    var2 = (digP[7] * p) / 524288.0
    
    p = (p + var1 + var2) / 256 + digP[6] * 16.0
    p = p / 256 / 100
    
    return p

#湿度補正
def bme280_compensate_h(adc_H):
    
    global t_fine

    var_H = float(t_fine) - 76800.0
    var_H = (adc_H - (float(digH[3]) * 64.0 + float(digH[4]) / 16384.0 * \
             var_H)) * (float(digH[1]) / 65536.0 * (1.0 + float(digH[5]) / \
             67108864.0 * var_H * (1.0 + float(digH[2]) / 67108864.0 * var_H)))
    var_H = var_H * (1.0 - float(digH[0]) * var_H / 524288.0)
    
    return var_H

#BME280の初期化
init_bme280()

#補正データ読み込み
read_compensate()

#測定データ読み込み  
read_data()
