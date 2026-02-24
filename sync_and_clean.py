import subprocess
import os
from datetime import datetime
from modules.maintenance import DataMaintenance 

class SyncManager:
    def __init__(self):
        self.server_user = "aelab-1" 
        self.server_hostname = "aelab-1-MS-7D18" 
        
        # 本地絕對路徑
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.local_runs_dir = os.path.join(self.base_dir, "runs")
        
        # 拆分遠端路徑，方便用指令建立目錄
        self.remote_folder = "~/Desktop/Jetson_Data"
        self.remote_dest_dir = f"{self.server_user}@{self.server_hostname}:{self.remote_folder}/"

        self.cleaner = DataMaintenance(
            img_dir=os.path.join(self.local_runs_dir, "images"),
            csv_path=os.path.join(self.local_runs_dir, "data_log.csv"),
            archive_dir=os.path.join(self.local_runs_dir, "history")
        )

    def _check_and_create_remote_dir(self):
        """透過 SSH 檢查並自動建立遠端資料夾"""
        print(f"[Sync] 檢查遠端伺服器目錄: {self.remote_folder} ...")
        # mkdir -p 代表：如果沒有就建立，如果有了就跳過
        ssh_cmd = ["ssh", f"{self.server_user}@{self.server_hostname}", f"mkdir -p {self.remote_folder}"]
        try:
            subprocess.run(ssh_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"[Sync Warning] 建立遠端目錄時發生異常: {e}")

    def run_sync(self):
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 啟動 SCP 傳輸模組...")
        
        # 🌟 新增的檢查機制：傳輸前先確保遠端有家可以回
        self._check_and_create_remote_dir()
        
        scp_cmd = ["scp", "-r", "-q", self.local_runs_dir, self.remote_dest_dir]
        
        try:
            result = subprocess.run(scp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                print("[Sync] 🎉 資料同步成功！檔案已送達伺服器。")
                self.post_sync_cleanup()
            else:
                print(f"[Sync Error] ❌ 同步失敗：\n{result.stderr}")
        except Exception as e:
            print(f"[Sync Exception] 程式發生未預期錯誤: {e}")

    def post_sync_cleanup(self):
        print("[Cleanup] 開始清理 Jetson 記憶體與過期資料...")
        self.cleaner.clean_old_images(days_to_keep=3)
        self.cleaner.archive_csv()
        self.cleaner.check_disk_usage()
        print("[Cleanup] 系統維護完成。")

if __name__ == "__main__":
    job = SyncManager()
    job.run_sync()
