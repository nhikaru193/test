import struct
import csv

def parse_line(line):
    try:
        if not line.strip():
            return None

        header, payload_str = line.strip().split(':')
        payload = [int(x) for x in payload_str.split(',')]

        # 緯度：35,97,24,70 → 35.972470
        latitude = float(f"{payload[2]}.{payload[3]:02d}{payload[4]:02d}{payload[5]:02d}")

        # 経度：51,39,83,04 → 5139.8304
        longitude = float(f"{payload[6]}{payload[7]:02d}.{payload[8]:02d}{payload[9]:02d}")

        return {
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

    # 緯度・経度のみをCSV出力
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['latitude', 'longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"緯度・経度のみを {output_file} に出力しました。")

if __name__ == '__main__':
    input_log = '/home/mark1/Desktop/im920_log.txt'   # 入力ファイル
    output_csv = '/home/mark1/Desktop/parsed_coords.csv'
    parse_log_file(input_log, output_csv)
