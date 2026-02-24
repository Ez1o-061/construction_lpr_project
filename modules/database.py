import csv
import os
import cv2
import time
from datetime import datetime

class DatabaseManager:
    def __init__(self, base_dir="runs", csv_name="data_log.csv", enable_scale_img=False):
        """
        將儲存邏輯統包：寫入 CSV，也負責將圖片存入硬碟
        """
        # 取得專案的絕對路徑，確保圖片不會因為執行終端機的位置不同而亂跑
        self.base_dir = os.path.abspath(base_dir)
        self.img_dir = os.path.join(self.base_dir, "images")
        self.file_path = os.path.join(self.base_dir, csv_name)
        self.enable_scale_img = enable_scale_img 
        
        # 自動建立絕對路徑的資料夾
        os.makedirs(self.img_dir, exist_ok=True)
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """確保 CSV 檔案存在，若不存在則建立並寫入標頭"""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            header = ["時間(Time)", "車牌狀態(Plate_Status)", "車牌(Plate)", "車牌照片(Plate_Image)", "地磅狀態(Scale_Status)", "重量(Weight_KG)"]
            if self.enable_scale_img: header.append("地磅照片(Scale_Image)")
                
            with open(self.file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(header)
            print(f"[Database] 已建立新資料庫: {self.file_path}")

    def save_record(self, plate_status, plate, frame, scale_status, weight, scale_img=None):
        """
        寫入一筆新資料 (儲存圖片並寫入 CSV)
        """
        try:
            # 1. 處理並儲存車牌圖片
            now_ts = int(time.time())
            img_filename = f"{plate}_{now_ts}.jpg"
            img_absolute_path = os.path.join(self.img_dir, img_filename)
            
            # 儲存到實體硬碟
            cv2.imwrite(img_absolute_path, frame)
            
            # CSV 存相對路徑，這樣傳到 Windows/Linux 伺服器上看才不會路徑錯亂
            relative_img_path = f"runs/images/{img_filename}"

            # 2. 寫入 CSV 紀錄
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row_data = [now_str, plate_status, plate, relative_img_path, scale_status, weight]
            if self.enable_scale_img: 
                row_data.append(scale_img if scale_img else "N/A")
                
            with open(self.file_path, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
                
            print(f"[Database] 成功儲存照片並寫入紀錄: {plate} | {weight}kg")
            return True
            
        except Exception as e:
            print(f"[Database] 寫入失敗: {e}")
            return False
