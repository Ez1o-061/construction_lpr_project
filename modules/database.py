import csv
import os
import cv2
import time
from datetime import datetime
import numpy as np # 建議引入 numpy 以協助判斷影像格式

class DatabaseManager:
    def __init__(self, base_dir="runs", csv_name="data_log.csv", enable_scale_img=False):
        """
        將儲存邏輯統包：寫入 CSV，也負責將圖片存入硬碟
        """
        self.base_dir = os.path.abspath(base_dir)
        self.img_dir = os.path.join(self.base_dir, "images")
        self.file_path = os.path.join(self.base_dir, csv_name)
        self.enable_scale_img = enable_scale_img 
        
        os.makedirs(self.img_dir, exist_ok=True)
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """確保 CSV 檔案存在，若不存在則建立並寫入標頭"""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            header = ["時間(Time)", "車牌狀態(Plate_Status)", "車牌(Plate)", "車牌照片(Plate_Image)", "地磅狀態(Scale_Status)", "重量(Weight_KG)"]
            if self.enable_scale_img: 
                header.append("地磅照片(Scale_Image)")
                
            with open(self.file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(header)
            print(f"[Database] 已建立新資料庫: {self.file_path}")

    def save_record(self, plate_status, plate, frame, scale_status, weight, scale_img=None):
        """
        寫入一筆新資料 (儲存圖片並寫入 CSV)
        """
        try:
            now_ts = int(time.time())
            
            # ==========================================
            # 1. 處理並儲存「車牌」圖片
            # ==========================================
            img_filename = f"{plate}_{now_ts}.jpg"
            img_absolute_path = os.path.join(self.img_dir, img_filename)
            
            # 儲存到實體硬碟
            cv2.imwrite(img_absolute_path, frame)
            
            # CSV 存相對路徑
            relative_img_path = f"runs/images/{img_filename}"

            # ==========================================
            # 2. 處理並儲存「地磅」圖片 (本次修正重點)
            # ==========================================
            relative_scale_img_path = "N/A"
            
            if self.enable_scale_img:
                # 檢查 scale_img 是否為有效的 OpenCV 影像 (具有 shape 屬性)
                if scale_img is not None and hasattr(scale_img, 'shape'):
                    scale_img_filename = f"scale_{plate}_{now_ts}.jpg"
                    scale_img_absolute_path = os.path.join(self.img_dir, scale_img_filename)
                    
                    # 儲存地磅照片到實體硬碟
                    cv2.imwrite(scale_img_absolute_path, scale_img)
                    
                    # CSV 存地磅照片的相對路徑
                    relative_scale_img_path = f"runs/images/{scale_img_filename}"
                elif scale_img is None:
                    # 系統開啟了地磅截圖功能，但沒有傳入圖片
                    print(f"[Database] 警告: 未收到地磅圖片 (車牌: {plate})")
                else:
                    print(f"[Database] 錯誤: 傳入的地磅影像格式不符 (車牌: {plate})")

            # ==========================================
            # 3. 寫入 CSV 紀錄
            # ==========================================
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row_data = [now_str, plate_status, plate, relative_img_path, scale_status, weight]
            
            if self.enable_scale_img: 
                row_data.append(relative_scale_img_path)
                
            with open(self.file_path, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
                
            print(f"[Database] 成功儲存照片並寫入紀錄: {plate} | {weight}kg")
            return True
            
        except Exception as e:
            print(f"[Database] 寫入失敗: {e}")
            return False

if __name__ == "__main__":
    # 簡單的單元測試
    import numpy as np
    db = DatabaseManager(enable_scale_img=True)
    
    # 建立假的影像陣列來模擬攝影機畫面
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dummy_scale = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 測試寫入
    db.save_record("Valid", "ABC-1234", dummy_frame, "Stable", 3500.0, scale_img=dummy_scale)
