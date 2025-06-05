#参考サイト
#https://www.serendip.ws/archives/5281
#https://keisan.casio.jp/exec/system/1257670779
#Vincenty法(逆解法)

import math

# 2地点間の方位角を計算
def direction(last_lng, location):
    x1 = math.radians(last_lng[0])
    y1 = math.radians(last_lng[1])
    x2 = math.radians(location[0])
    y2 = math.radians(location[1])

    delta_y = y2 - y1
    #print("delta_y", delta_y)

    phi = math.atan2(math.sin(delta_y), math.cos(x1) * math.tan(x2) - math.sin(x1) * math.cos(delta_y))
    phi = math.degrees(phi)
    angle = (phi + 360) % 360
    #print("phi =", phi)
    return abs(angle) + (1 / 7200.0) #単位は°

# 2地点間の距離を計算
def distance(current_location, destination_location):
    x1 = math.radians(current_location[0])
    y1 = math.radians(current_location[1])
    x2 = math.radians(destination_location[0])
    y2 = math.radians(destination_location[1])

    radius = 6378137.0

    dist = radius * math.acos(math.sin(y1) * math.sin(y2) + math.cos(y1) * math.cos(y2) * math.cos(x2 - x1))

    return dist #単位はメートル

# 使用例
'''
current_location = (35.6544, 139.74477)  # Tokyo
destination_location = (21.4225, 39.8261)  # New York
direction_angle = direction(current_location, destination_location)
direction_distance =distance(current_location, destination_location)
print("Angle:", direction_angle)
print("Distance:", direction_distance)
'''
