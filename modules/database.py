import csv
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, file_path="runs/data_log.csv", enable_scale_img=False):
        """
        土資場資料庫管理器 (CSV 模組化版本)
        Args:
            file_path: 檔案儲存路徑
            enable_scale_img (bool): 是否啟用「地磅照片」欄位 (True/False)
        """
        self.file_path = file_path
        self.enable_scale_img = enable_scale_img # 控制是否寫入地磅照片
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """確保 CSV 檔案存在，若不存在則建立並寫入標頭 (Header)"""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # 依據是否開啟地磅照片，動態生成標題
            header = [
                "時間(Time)", 
                "車牌狀態(Plate_Status)", 
                "車牌(Plate)", 
                "車牌照片(Plate_Image)", 
                "地磅狀態(Scale_Status)", 
                "重量(Weight_KG)"
            ]
            if self.enable_scale_img:
                header.append("地磅照片(Scale_Image)")
                
            with open(self.file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(header)
            print(f"[Database] 已建立新資料庫: {self.file_path}")

    def save_record(self, plate_status, plate, plate_img, scale_status, weight, scale_img=None):
        """
        寫入一筆新資料
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 組裝 Tuple/List 資料
        row_data = [
            now, 
            plate_status, 
            plate, 
            plate_img, 
            scale_status, 
            weight
        ]
        
        # 若參數有開啟地磅照片功能，才將其加入寫入序列
        if self.enable_scale_img:
            row_data.append(scale_img if scale_img else "N/A")
            
        try:
            with open(self.file_path, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
            print(f"[Database] 成功寫入: {plate} | {weight}kg")
            return True
        except Exception as e:
            print(f"[Database] 寫入失敗: {e}")
            return False
