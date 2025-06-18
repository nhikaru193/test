import cv2
import numpy as np
import math

#円形度計算関数の定義
def calculate_circularity(contour):
    area = cv2.contourArea(contour)                    #輪郭が囲む面積を求める
    perimeter = cv2.arcLength(contour, True)           #輪郭の周囲長を計算　(対象関数, 輪郭が閉じているか)
    if perimeter == 0:                                 #保険(周囲長==０)
        return 0
    return 4 * math.pi * area / (perimeter * perimeter)#円形度の公式(円形度を用い、円を検出するため)
 
#図形形状判別アルゴリズムの定義
def classify_shape(contour):                           
    epsilon = 0.02 * cv2.arcLength(contour, True)      #数値×周囲長　(周囲長×数値分の精度
    approx = cv2.approxPolyDP(contour, epsilon, True)  #頂点リスト算出(x1, y1), (x2, y2)などのこと　(対象関数, 精度, 輪郭が閉じているか)　
    vertices = len(approx)                             #len(対象関数)の対象関数に含まれる頂点の数を数値として格納  座標の数を数値として格納                   
    area = cv2.contourArea(contour)                    #輪郭の囲む面積を算出

    #面積の小さな図形はカットする
    if area < 100:
        return None, approx
    
    #円形度計算(この関数は定義済み)
    circularity = calculate_circularity(contour)
 
    #
    aspect_ratio = None                                #noneを格納　後にこの関数を使用するため
    if len(contour) >= 5:                              #輪郭点が5以上でないと楕円作成不可能
        ellipse = cv2.fitEllipse(contour)              #fitEllipse()は一番近い楕円の作成
        (center, axes, orientation) = ellipse          #3つの変数に展開して代入
        major_axis, minor_axis = max(axes), min(axes)  #楕円の長径
        aspect_ratio = major_axis / minor_axis if minor_axis != 0 else None  #アスペクト比算出
 
    #頂点数と円形度、アスペクト比を用いた図形の特定、分類、出力
    shape = "不明"
    if vertices == 3:
        shape = "三角形"
    elif vertices == 4:
        x, y, w, h = cv2.boundingRect(approx)
        ar = float(w) / h
        if 0.95 <= ar <= 1.05:
            shape = "正方形"
        else:
            shape = "長方形"
    elif vertices == 5:
        shape = "五角形"
    elif vertices == 6:
        shape = "六角形"
    else:
        if circularity > 0.85:
            if aspect_ratio is not None and 0.9 <= aspect_ratio <= 1.1:
                shape = "円形"
            else:
                shape = "楕円"
        else:
            shape = "多角形"
 
    return shape, approx
 
# 画像読み込み
cap = cv2.VideoCapture(0)  # Pi カメラモジュールV3に接続されたカメラデバイス
if not cap.isOpened():
    print("カメラが見つかりません。接続と設定を確認してください。")
    exit()

while True:
    ret, img = cap.read()
    if not ret:
        print("フレームが取得できませんでした。")
        break

#画像読み込みに難ありの場合(大体onedriveのセキュリティ的な問題かfile名の問題)
　　if img is None:
        print("画像が読み込めませんでした。パスを確認してください！")
        exit()

#imgの(高さ, 幅, チャンネル数)の前半2値を取得する
    height, width = img.shape[:2] #[:n]でn値の取得

# 横方向3分割の幅
    grid_cols = 3                                   #後に使う
    block_w = width // grid_cols                    #各ブロックの幅を計算
 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)    #imgをCOLOR_BGR2GRAY方式でグレースケールの作成
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)     #(対象関数, (幅), 標準偏差) (5, 5)となっているが(7,7)とすれば強いぼかし。奇数だよ！
     #canny法で輪郭検出
    edges = cv2.Canny(blurred, 50, 150)             #(対象関数, 最小閾値, 最大閾値)　最大閾値以上→エッジ認識、最小閾値以下→認識せず、それ以外→周囲にエッジがあれば白


    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
 
# ブロック名（ラベル）を用意
    block_names = {0: "左", 1: "中央", 2: "右"}
 
# 各ブロックに検出図形のリストを格納する辞書
    blocks_shapes = {0: [], 1: [], 2: []}
 
    for cnt in contours:
      shape, approx = classify_shape(cnt)
      if shape is None:
          continue
      x, y, w, h = cv2.boundingRect(approx)
      cx = x + w // 2
 
    # 横方向3分割でどのブロックに属するか判定
      block_idx = min(cx // block_w, grid_cols - 1)
      blocks_shapes[block_idx].append(shape)
 
    # 図形描画
      cv2.drawContours(img, [approx], -1, (0, 255, 0), 2)
      cv2.putText(img, shape, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
 
# 3ブロックの区切り線を描画
    for i in range(1, grid_cols):
        cv2.line(img, (i * block_w, 0), (i * block_w, height), (255, 0, 0), 2)
 
# 各ブロックの図形をテキストで表示
    for i in range(grid_cols):
        shapes_in_block = blocks_shapes[i]
        if not shapes_in_block:
            continue
        counts = {}
        for s in shapes_in_block:
            counts[s] = counts.get(s, 0) + 1
 
        text = ", ".join([f"{k}:{v}" for k, v in counts.items()])
    # テキスト表示位置（ブロックの上部中央あたり）
        text_x = i * block_w + 10
        text_y = 30
        cv2.putText(img, f"{block_names[i]}: {text}", (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
 
# ターミナルにも各ブロックの図形情報を出力
    for i in range(grid_cols):
        shapes_in_block = blocks_shapes[i]
        if not shapes_in_block:
            print(f"{block_names[i]}: 図形なし")
            continue
        counts = {}
        for s in shapes_in_block:
            counts[s] = counts.get(s, 0) + 1
 
        text = ", ".join([f"{k}:{v}" for k, v in counts.items()])
        print(f"{block_names[i]}: {text}")

    cv2.imshow("Shape Detection - Live", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

 
cap.release()
cv2.imshow("Shape Detection - 3分割", img)
cv2.imshow("Edges", edges)
cv2.waitKey(0)
cv2.destroyAllWindows()
