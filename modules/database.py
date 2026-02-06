import csv
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, file_path="runs/data_log.csv"):
        """
        簡易資料儲存管理器 (CSV 版本)
        直接儲存為 Excel 可開啟的格式
        """
        self.file_path = file_path
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """確保 CSV 檔案存在，若不存在則建立並寫入標頭 (Header)"""
        if not os.path.exists(self.file_path):
            # 確保父目錄存在
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # 寫入欄位名稱 (Excel 的第一列)
            with open(self.file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "時間 (Time)", "車牌號碼 (Plate)", "重量 (Weight KG)", "圖片路徑 (Image)"])
            print(f"[System] Created new data log: {self.file_path}")

    def save_record(self, plate, weight, img_path):
        """寫入一筆新資料"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open(self.file_path, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 自動計算 ID (雖然 CSV 沒有自動增量，但我們可以省略或用行數)
                # 這裡簡單留空 ID 或用 timestamp 當 ID
                writer.writerow(["-", now, plate, weight, img_path])
                
            print(f"[Data] Saved to Excel: {plate} | {weight}kg")
            return True
        except Exception as e:
            print(f"[Data] Save Error: {e}")
            return False

    def close(self):
        # CSV 模式下不需要特別關閉連線，但保留此函式以相容主程式
        pass

if __name__ == "__main__":
    # 測試
    db = DatabaseManager("test_log.csv")
    db.save_record("TEST-8888", 3500.0, "test.jpg")
    print("測試完成，請打開 test_log.csv 檢查")
