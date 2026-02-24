import subprocess
import os
from datetime import datetime
from modules.maintenance import DataMaintenance 

class SyncManager:
    def __init__(self):
        # === 伺服器端設定 (學校電腦 / Windows 測試機) ===
        #self.server_user = "User"
        #self.server_hostname = "desktop-ez1o" # Tailscale MagicDNS
        self.server_user = "aelab-1" 
        self.server_hostname = "aelab-1-MS-7D18" # Tailscale MagicDNS
	
        # 邊緣端 (Jetson) 資料夾路徑
        self.local_runs_dir = "/home/ez1o/Desktop/construction_lpr_project/runs"
        
        # Windows 伺服器接收路徑
        #self.remote_dest_dir = f"{self.server_user}@{self.server_hostname}:C:/Jetson_Data/"
	# Linux 伺服器接收路徑
        self.remote_dest_dir = f"{self.server_user}@{self.server_hostname}:~/Desktop/Jetson_Data/"

        # 初始化清理模組
        self.cleaner = DataMaintenance(
            img_dir=f"{self.local_runs_dir}/images",
            csv_path=f"{self.local_runs_dir}/data_log.csv",
            archive_dir=f"{self.local_runs_dir}/history"
        )

    def run_sync(self):
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 啟動 SCP 傳輸模組...")
        
        # 執行 scp 遞迴傳輸指令
        scp_cmd = [
            "scp", "-r", "-q", 
            self.local_runs_dir, 
            self.remote_dest_dir
        ]
        
        try:
            # 呼叫系統底層執行傳輸
            result = subprocess.run(scp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                print("[Sync] 資料同步成功！檔案已送達伺服器。")
                # 傳輸成功後，觸發記憶體清理機制
                self.post_sync_cleanup()
            else:
                print(f"[Sync Error] 同步失敗，錯誤訊息：\n{result.stderr}")
                
        except Exception as e:
            print(f"[Sync Exception] 程式發生未預期錯誤: {e}")

    def post_sync_cleanup(self):
        print("[Cleanup] 開始清理 Jetson 記憶體與過期資料...")

        # 1. 清理過期圖片 (因為每次都會備份到 Windows，邊緣端保留 3 天即可)
        self.cleaner.clean_old_images(days_to_keep=3)

        # 2. 封存目前的 CSV
        self.cleaner.archive_csv()

        # 3. 檢查硬碟空間是否安全
        self.cleaner.check_disk_usage()
        print("[Cleanup] 系統維護完成。")

if __name__ == "__main__":
    sync_job = SyncManager()
    sync_job.run_sync()
