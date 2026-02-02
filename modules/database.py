import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="site_data.db"):
        """
        資料庫管理模組 (SQLite)
        Args:
            db_name (str): 資料庫檔案路徑
        """
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_table()

    def connect(self):
        """建立資料庫連線"""
        try:
            # check_same_thread=False 允許在不同執行緒中使用 (對應 GUI 或 Web 應用)
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self.cursor = self.conn.cursor()
            print(f"[DB] Connected to {self.db_name}")
        except sqlite3.Error as e:
            print(f"[DB] Connection error: {e}")

    def create_table(self):
        """初始化資料表結構"""
        sql = """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            plate_number TEXT,
            weight_kg REAL,
            image_path TEXT
        );
        """
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[DB] Init table error: {e}")

    def save_record(self, plate, weight, img_path):
        """
        儲存一筆紀錄
        Args:
            plate (str): 車牌號碼
            weight (float): 重量
            img_path (str): 圖片存檔路徑
        Returns:
            bool: 成功回傳 True，失敗回傳 False
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = "INSERT INTO records (timestamp, plate_number, weight_kg, image_path) VALUES (?, ?, ?, ?)"
        try:
            self.cursor.execute(sql, (now, plate, weight, img_path))
            self.conn.commit()
            print(f"[DB] Saved record: {plate} | {weight}kg")
            return True
        except sqlite3.Error as e:
            print(f"[DB] Insert error: {e}")
            return False

    def close(self):
        """關閉資料庫連線"""
        if self.conn:
            self.conn.close()
            print("[DB] Connection closed")

# --- 單元測試區塊 ---
if __name__ == "__main__":
    print("[DB] Running module self-check...")
    test_db_name = "test_temp.db"
    
    # 測試寫入
    db = DatabaseManager(test_db_name)
    success = db.save_record("TEST-8888", 5000.0, "/tmp/test.jpg")
    
    # 測試驗證
    if success:
        print("[DB] Write test passed.")
    else:
        print("[DB] Write test failed.")
        
    db.close()
    
    # 清除測試檔案
    if os.path.exists(test_db_name):
        os.remove(test_db_name)
        print("[DB] Test file cleaned up.")
