x = L76X.L76X()
x.L76X_Set_Baudrate(9600)
x.L76X_Send_Command(x.SET_POS_FIX_1000MS)  # 1秒ごとに更新
x.L76X_Send_Command(x.SET_NMEA_OUTPUT)
x.L76X_Exit_BackupMode()

while True:
    x.L76X_Gat_GNRMC()
    if x.Status == 1:
        print('位置取得成功')
        print('UTC時刻: {:02}:{:02}:{:02}'.format(x.Time_H, x.Time_M, int(x.Time_S)))
        print('緯度: {:.6f}, 経度: {:.6f}'.format(x.Lat, x.Lon))
    else:
        print('位置未取得')
