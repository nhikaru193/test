import struct
import csv

def parse_line(line):
    try:
        # 空行や":"が含まれない行はスキップ
        if not line.strip() or ':' not in line:
            return None

        header, payload_str = line.strip().split(':')
        parts = header.split(',')

        if len(parts) < 3:
            return None

        node = parts[1]
        rssi_hex = parts[2]
        try:
            rssi = int(rssi_hex, 16)
        except ValueError:
            return None

        # カンマ区切りされた16進値をバイト列へ
        hex_values = payload_str.strip().split(',')
        if len(hex_values) < 10:  # 最低限: ヘッダ1 + 緯度4 + 経度4 + 予備1（最低9バイト必要）
            return None

        try:
            payload_bytes = bytes(int(x, 16) for x in hex_values)
        except ValueError:
            return None

        # バイト長チェック（少なくとも9バイト必要）
        if len(payload_bytes) < 9:
            return None

        # 緯度: バイト2〜5（4バイト） 経度: バイト6〜9（4バイト）
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

    if not results:
        print("有効なデータが見つかりませんでした。")
        return

    # CSV出力
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['node', 'rssi', 'latitude', 'longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"解析成功: {len(results)} 件を {output_file} に保存しました。")

if __name__ == '__main__':
    input_log = '/home/mark1/Desktop/im920_log.txt'
    output_csv = '/home/mark1/Desktop/parsed_coords.csv'
    parse_log_file(input_log, output_csv)
