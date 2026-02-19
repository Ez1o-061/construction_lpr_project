import Jetson.GPIO as GPIO
import threading
from multiprocessing import Queue
import queue
import time

from button import Button
# 替換成你寫好的控制器
from system_controller import SystemController

def listen_button(btn, q):
    """獨立執行緒：負責監聽硬體按鈕並將訊號放入 Queue"""
    while True:
        listen = btn.get_push()
        if listen:
            try: 
                # 將切換訊號放入 Queue，timeout 設為 1 秒
                q.put(True, timeout=1) 
                btn.know() # 確認資訊確實傳出去，重置按鈕狀態
            except queue.Full:
                print("[System] Queue 已滿，忽略本次按鍵")
                continue
        time.sleep(0.1) # 釋放 CPU 資源

if __name__ == "__main__":
    print("=== 啟動土資場車牌辨識系統 ===")
    
    # 1. 建立進程間通訊的 Queue
    q = Queue(maxsize=5)

    # 2. 建立並「啟動」你的 SystemController 子進程
    # 注意：這裡的 model_path 記得確認實際路徑
    main_process = SystemController(q, model_path="laptop.engine")
    main_process.start() # [修正] 補上啟動指令
    print("[System] AI 子進程已啟動")

    # 3. 初始化按鈕與監聽執行緒
    # 假設同事的 button.py 邏輯沒變，BCM pin 15
    try:
        license_show_switch = Button(15) 
        # [修正] 語法錯誤與加入 daemon (主程式關閉時跟著關閉)
        th_btn = threading.Thread(target=listen_button, args=(license_show_switch, q), daemon=True)
        th_btn.start()
        print("[System] 按鈕監聽執行緒已啟動")
    except Exception as e:
        print(f"[System] 按鈕初始化失敗，請檢查硬體接線: {e}")

    # 4. 主迴圈：監控系統健康狀態與釋放資源
    try:
        while True:
            # 每秒檢查一次 AI 進程是否還存活
            if not main_process.is_alive():
                print("[System Error] AI 進程意外終止！")
                break
            time.sleep(1) # [修正] 避免 CPU 空轉

    except KeyboardInterrupt:
        # 優雅關機 (Graceful Shutdown)
        print("\n[System] 接收到終止訊號 (Ctrl+C)，準備安全關機...")
    
    finally:
        # 清理所有資源
        main_process.terminate()
        main_process.join()
        try:
            GPIO.cleanup()
        except:
            pass
        print("[System] 系統已安全關閉")
