import os
import time
import shutil
import glob
from datetime import datetime

class DataMaintenance:
    def __init__(self, img_dir="runs/images", csv_path="runs/data_log.csv", archive_dir="runs/history"):
        """
        資料維護模組
        Args:
            img_dir: 圖片儲存路徑
            csv_path: CSV 資料庫路徑
            archive_dir: CSV 歸檔路徑 (舊資料移到這裡)
        """
        self.img_dir = img_dir
        self.csv_path = csv_path
        self.archive_dir = archive_dir
        
        # 確保目錄存在
        os.makedirs(self.img_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

    def clean_old_images(self, days_to_keep=7):
        """
        刪除超過 N 天的圖片
        """
        now = time.time()
        cutoff = now - (days_to_keep * 86400) # 86400秒 = 1天
        
        count = 0
        deleted_size_mb = 0
        
        # 取得所有 jpg 檔案
        files = glob.glob(os.path.join(self.img_dir, "*.jpg"))
        
        print(f"[Maintenance] 檢查圖片過期狀況 (保留 {days_to_keep} 天)...")
        
        for f in files:
            try:
                # 檢查檔案修改時間
                if os.path.getmtime(f) < cutoff:
                    size = os.path.getsize(f)
                    os.remove(f)
                    count += 1
                    deleted_size_mb += size
            except Exception as e:
                print(f"[Error] 無法刪除 {f}: {e}")

        deleted_size_mb /= (1024 * 1024)
        print(f"[Maintenance] 已刪除 {count} 張過期圖片，釋放空間: {deleted_size_mb:.2f} MB")

    def archive_csv(self):
        """
        將目前的 CSV 封存並重開一個新的
        例如: data_log.csv -> runs/history/data_log_20250207.csv
        """
        if not os.path.exists(self.csv_path):
            print("[Maintenance] CSV 檔案不存在，無需封存")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(self.csv_path)
        name, ext = os.path.splitext(filename)
        
        new_name = f"{name}_{timestamp}{ext}"
        dest_path = os.path.join(self.archive_dir, new_name)
        
        try:
            shutil.move(self.csv_path, dest_path)
            print(f"[Maintenance] CSV 已封存至: {dest_path}")
            # 注意：這裡不需建立新檔，DatabaseManager下次啟動時會自動建立
        except Exception as e:
            print(f"[Error] CSV 封存失敗: {e}")

    def check_disk_usage(self, warning_percent=90):
        """檢查硬碟空間，若不足則發出警告"""
        total, used, free = shutil.disk_usage("/")
        
        # 轉成 GB
        total_gb = total // (2**30)
        free_gb = free // (2**30)
        percent_used = (used / total) * 100
        
        print(f"[System] 硬碟空間: {percent_used:.1f}% 已用 (剩餘 {free_gb} GB)")
        
        if percent_used > warning_percent:
            print(f"[WARNING] 硬碟空間不足！建議立即清理！")
            return False # 空間不足
        return True # 空間足夠

if __name__ == "__main__":
    # 單元測試
    cleaner = DataMaintenance()
    cleaner.check_disk_usage()
    # cleaner.clean_old_images(days_to_keep=30) # 測試時小心不要刪到重要資料
