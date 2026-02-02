import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="site_data.db"):
        """
        資料庫管理員
        :param db_name: 資料庫檔案名稱
        """
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        
        # 初始化時自動連線並建表
        self.connect()
        self.create_table()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self.cursor = self.conn.cursor()
            print(f"✅ [DB] 資料庫已連接: {self.db_name}")
        except sqlite3.Error as e:
            print(f"❌ [DB] 連線失敗: {e}")

    def create_table(self):
        """如果資料表不存在，就建立它"""
        create_sql = """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            plate_number TEXT,
            weight_kg REAL,
            image_path TEXT
        );
        """
        try:
            self.cursor.execute(create_sql)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ [DB] 建表失敗: {e}")

    def save_record(self, plate, weight, img_path):
        """
        儲存一筆紀錄
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        insert_sql = """
        INSERT INTO records (timestamp, plate_number, weight_kg, image_path)
        VALUES (?, ?, ?, ?)
        """
        try:
            self.cursor.execute(insert_sql, (now, plate, weight, img_path))
            self.conn.commit()
            print(f"💾 [DB] 紀錄已儲存: {plate} | {weight}kg")
            return True
        except sqlite3.Error as e:
            print(f"❌ [DB] 寫入失敗: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            print("🔴 [DB] 連線已關閉")

# --- 單元測試 ---
if __name__ == "__main__":
    print("🔧 進入資料庫測試模式...")
    db = DatabaseManager("test_data.db")
    
    # 測試寫入
    print("✍️ 正在寫入測試資料...")
    db.save_record("TEST-8888", 3500.5, "/tmp/test.jpg")
    db.save_record("ABC-1234", 12000.0, "/tmp/truck.jpg")
    
    # 測試讀取 (驗證寫入是否成功)
    print("📖 讀取資料驗證:")
    cursor = db.conn.execute("SELECT * FROM records")
    for row in cursor:
        print(f"   -> {row}")
    
    db.close()
    
    # 測試完刪除暫存檔
    if os.path.exists("test_data.db"):
        os.remove("test_data.db")
        print("🧹 測試資料庫已清除")
