import struct
import csv

def parse_line(line):
    try:
        # 空行や不正行はスキップ
        if not line.strip():
            return None

        header, payload_str = line.strip().split(':')
        parts = header.split(',')

        node = parts[1]           # 送信元ノード番号
        rssi = int(parts[2], 16)  # RSSI

        # ペイロードの16進数文字列 → バイト列
        payload_bytes = bytes(int(x, 16) for x in payload_str.split(','))

        # 緯度・経度はバイト2〜5と6〜9の4バイトずつ（ビッグエンディアン符号付き整数）
        lat_bytes = payload_bytes[2:9]
        lon_bytes = payload_bytes[10:18]

        lat_fixed = struct.unpack(">i", lat_bytes)[0]
        lon_fixed = struct.unpack(">i", lon_bytes)[0]

        latitude = lat_fixed / 1_000_000
        longitude = lon_fixed / 1_000_000

        return {
            'node': node,
            'rssi': rssi,
            'latitude': latitude,
            'longitude': longitude
        }
    except Exception as e:
        print(f"解析エラー: {e} 行: {line}")
        return None

def parse_log_file(input_file, output_file):
    results = []
    with open(input_file, 'r') as f:
        for line in f:
            parsed = parse_line(line)
            if parsed:
                results.append(parsed)

    # CSV出力
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['node', 'rssi', 'latitude', 'longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"解析結果を {output_file} に出力しました。")

if __name__ == '__main__':
    input_log = '/home/mark1/Desktop/im920_log.txt'# 解析したいログファイル名
    output_csv = '/home/mark1/Desktop/parsed_coords.csv'
    parse_log_file(input_log, output_csv)
