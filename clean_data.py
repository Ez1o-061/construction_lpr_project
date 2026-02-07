from modules.maintenance import DataMaintenance

def main():
    print("=== 系統數據清理工具 ===")
    print("1. 清理舊圖片 (保留最近 7 天)")
    print("2. 封存目前的 CSV 報表")
    print("3. 全部執行")
    print("4. 離開")
    
    choice = input("請選擇功能 (1-4): ")
    
    cleaner = DataMaintenance()
    
    if choice == '1':
        days = input("要保留幾天內的圖片? (預設 7): ")
        if not days: days = 7
        cleaner.clean_old_images(days_to_keep=int(days))
        
    elif choice == '2':
        cleaner.archive_csv()
        
    elif choice == '3':
        cleaner.archive_csv()
        cleaner.clean_old_images(days_to_keep=7)
        cleaner.check_disk_usage()
        
    else:
        print("離開")

if __name__ == "__main__":
    main()
