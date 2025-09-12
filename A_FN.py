
import time
import smbus
import struct
import os #save fileのときに使用
import csv
import cv2
import math
import numpy as np
from picamera2 import Picamera2
from A_BNO055 import BNO055
from A_Motor import MotorDriver
from A_Flag_B import Flag_B
#import RPi.GPIO as GPIO
from collections import deque

class FN:
    # --- クラスの初期化メソッド ---
    def __init__(self, bno: BNO055, driver, flag_location, pi):
        
        # --- 設定値 ---
        self.TARGET_SHAPES = ["三角形", "長方形", "T字"] #"三角形", "長方形", "T字", "十字"を追加する
        self.AREA_THRESHOLD_PERCENT = 3.5
        self.turn_speed = 95
        self.F_lat = flag_location[0]
        self.F_lon = flag_location[1]

        # --- 初期化処理 ---
        self.detector = Flag_B(triangle_tolerance=0.5)
        self.driver = driver
        """
        self.driver = MotorDriver(
            PWMA=12, AIN1=23, AIN2=18,      
            PWMB=19, BIN1=16, BIN2=26,      
            STBY=21                       
        )
        """
        self.screen_area = self.detector.width * self.detector.height
        self.pi = pi
        # === BNO055 初期化 ===
        self.bno = bno

    def find_target_flag(self, detected_data, target_name):
        """検出データから指定された図形(target_name)のフラッグを探して返す"""
        for flag in detected_data:
            for shape in flag['shapes']:
                if shape['name'] == target_name:
                    return flag
        return None

    # === 追加したヘルパー関数 ===
    def get_shape_from_flag(self, flag_data, shape_name):
        """
        指定されたフラッグデータの中から、目的の図形データを検索して返す
        """
        if 'shapes' in flag_data:
            for shape in flag_data['shapes']:
                if shape['name'] == shape_name:
                    return shape
        return None

    def run(self):
        """
        全てのターゲットフラッグを探索し、接近するメインのタスクを実行
        """
        # --- CSVファイルの設定：ループの外側で一度だけファイルを開く ---
        current_time_str = time.strftime("%m%d-%H%M%S") #現在時刻をファイル名に含める
        path_to = "/home/EMA/_csv"
        filename = os.path.join(path_to, f"Flag_NAVIGATE_{current_time_str}.csv")

        # 'with'構文でファイルを開き、処理が終われば自動で閉じる
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            # ヘッダー行を最初に一度だけ書き込む
            writer.writerow(["target_name", "final_area_percent"])

            # --- 全てのターゲットに対してループ ---
            for target_name in self.TARGET_SHAPES:
                print(f"\n---====== 新しい目標: [{target_name}] の探索を開始します ======---")
                
                task_completed = False
                # スタック判定のために方位角を保存するdeque
                heading_history = deque(maxlen=4) # 直近3回の回転後の方位を記録
                
                while not task_completed:
                    
                    # --- 探索 ---
                    print(f"[{target_name}] を探しています...")
                    detected_data = self.detector.detect()
                    target_flag = self.find_target_flag(detected_data, target_name)

                    # 見つからない場合は回転して探索
                    if target_flag is None:
                        print(f"[{target_name}] が見つかりません。回転して探索します。")
                        search_count = 0
                        
                        while target_flag is None and search_count < 10:
                            self.driver.petit_petit(5)
                            self.driver.petit_left(0, self.turn_speed)
                            self.driver.petit_left(self.turn_speed, 0)
                            self.driver.motor_stop_brake()
                            time.sleep(0.3)
                            detected_data = self.detector.detect()
                            target_flag = self.find_target_flag(detected_data, target_name)
                            time.sleep(0.5)
                            search_count += 1
                            
                        rotation_count = 0
                        while target_flag is None and rotation_count < 22:
                            
                            self.driver.petit_right(0, 95)
                            self.driver.petit_right(95, 0)
                            self.driver.motor_stop_brake()
                            time.sleep(0.3)
                            
                            detected_data = self.detector.detect()
                            target_flag = self.find_target_flag(detected_data, target_name)
                            time.sleep(0.5)
                            rotation_count += 1
                            
                    # 回転しても見つからなかったら、このターゲットは諦めて次の輪郭検知
                    if target_flag is None:
                        print(f"探索しましたが [{target_name}] は見つかりませんでした。次の目標に移ります。")
                        break # while not task_completed ループを抜ける

                    # --- 追跡（中央寄せ＆接近）---
                    print(f"[{target_name}] を発見！追跡を開始します。")
                    while target_flag:
                        # --- 中央寄せ ---
                        if target_flag['location'] != '中央':
                            print(f"位置を調整中... (現在位置: {target_flag['location']})")
                            if target_flag['location'] == '左':
                                self.driver.petit_left(0, self.turn_speed)
                                self.driver.petit_left(self.turn_speed, 0)
                                self.driver.motor_stop_brake()
                                time.sleep(0.3)
                            elif target_flag['location'] == '右':
                                self.driver.petit_right(0, self.turn_speed)
                                self.driver.petit_right(self.turn_speed, 0)
                                self.driver.motor_stop_brake()
                                time.sleep(0.3)
                            
                            # 動かした直後に再検出
                            print("  再検出中...")
                            detected_data = self.detector.detect()
                            target_flag = self.find_target_flag(detected_data, target_name)
                            
                            if not target_flag:
                                print(f"調整中に [{target_name}] を見失いました。")
                                break # 追跡ループを抜ける
                            
                            # 位置を再評価するため、ループの最初に戻る
                            continue
                        
                        # --- 接近 ---
                        else: # 中央にいる場合
                            target_shape_data = self.get_shape_from_flag(target_flag, target_name)

                            if target_shape_data and 'contour' in target_shape_data:
                                shape_area = cv2.contourArea(target_shape_data['contour'])
                                area_percent = (shape_area / self.screen_area) * 100
                                print(f"中央に補足。接近中... (図形 '{target_name}' の画面占有率: {area_percent:.1f}%)")

                                if area_percent >= self.AREA_THRESHOLD_PERCENT:
                                    print(f"[{target_name}] に接近完了！")
                                    task_completed = True
                                    
                                    # --- ★★★ データをCSVに書き込む ★★★ ---
                                    writer.writerow([target_name, f"{area_percent:.2f}"])
                                    f.flush() # バッファを即時書き込み
                                    
                                    time.sleep(1)
                                    break # 追跡ループを抜ける
                                else:
                                    # しきい値未満なら、前進
                                    self.driver.petit_petit(3)
                            
                            else:
                                print(f"エラー: [{target_name}]は中央にありますが、その図形データがありません。再探索します。")
                                break 

                        # 動作後に再検出
                        print("  再検出中...")
                        detected_data = self.detector.detect()
                        target_flag = self.find_target_flag(detected_data, target_name)
                        
                        if not target_flag:
                            print(f"追跡中に [{target_name}] を見失いました。再探索します。")
                            break

        print("\n---====== 全ての目標の探索が完了しました ======---")
        # --- クリーンアップ処理 ---
        self.cleanup()
        
    def cleanup(self):
        """プログラム終了時にリソースを解放します。"""
        print("--- 制御を終了します ---")
        self.detector.close()
        # GPIO.cleanup()はdriver.cleanup()内で呼ばれることが多いので、重複していれば片方でOK
