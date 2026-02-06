import cv2
import threading
import time
import os
import subprocess
from queue import Queue, Full, Empty
from datetime import datetime

# 引入所有模組
from modules.camera import CameraDriver
from modules.lpr_ai import LPRSystem
from modules.scale import ScaleDriver
from modules.database import DatabaseManager
from modules.button import Button
from modules.button_power import ButtonPower

# --- 設定區 ---
CAMERA_ID = 0
BTN_MODE_PIN = 24  # 請確認實際接腳
BTN_POWER_PIN = 25 # 請確認實際接腳
SAVE_COOLDOWN = 5.0 # 同一台車幾秒內不重複存檔

def main():
    # 1. 初始化系統模組
    print("[System] Initializing modules...")
    
    # 硬體
    cam = CameraDriver(camera_id=CAMERA_ID)
    scale = ScaleDriver(simulate=True) # 若接上地磅，改為 simulate=False
    
    # 按鈕 (包在 try-except 防止 GPIO 權限問題導致程式崩潰)
    try:
        btn_mode = Button(pin=BTN_MODE_PIN)
        btn_power = ButtonPower(pin=BTN_POWER_PIN)
    except Exception as e:
        print(f"[System] GPIO Init Failed: {e}. Using software defaults.")
        btn_mode = None
        btn_power = None

    # 軟體 (AI & DB)
    ai_system = LPRSystem() 
    db = DatabaseManager()

    # 2. 建立多執行緒通訊機制
    frame_queue = Queue(maxsize=1)  # 存放待辨識影像
    result_queue = Queue(maxsize=1) # 存放辨識結果
    stop_event = threading.Event()  # 用來安全停止所有執行緒

    # ---------------------------
    # AI 工作執行緒 (Worker Thread)
    # ---------------------------
    def ai_worker():
        print("[AI Worker] Started.")
        while not stop_event.is_set():
            try:
                # 等待影像輸入 (timeout 避免卡死無法退出)
                frame = frame_queue.get(timeout=0.1)
                
                # 執行辨識
                annotated_frame, best_text = ai_system.process_frame(frame)
                
                # 將結果送回主執行緒
                if result_queue.full():
                    try: result_queue.get_nowait() # 丟棄舊結果
                    except Empty: pass
                result_queue.put((annotated_frame, best_text))
                
            except Empty:
                continue
            except Exception as e:
                print(f"[AI Worker] Error: {e}")
        print("[AI Worker] Stopped.")

    # 啟動 AI 執行緒
    ai_thread = threading.Thread(target=ai_worker, daemon=True)
    ai_thread.start()

    # ---------------------------
    # 主迴圈 (Main Loop)
    # ---------------------------
    print("[System] Ready. Press ESC to exit.")
    
    # 狀態變數
    current_mode = "DETECTION"
    last_save_time = 0
    last_plate_text = ""

    try:
        while True:
            # A. 檢查電源與按鈕狀態
            if btn_power and btn_power.get_mode() == "POWER_OFF":
                print("[System] Shutdown signal received!")
                stop_event.set()
                # 執行關機 (需 root 權限或 sudo免密碼)
                subprocess.run(['sudo', 'shutdown', '-h', 'now'])
                break
            
            if btn_mode:
                current_mode = btn_mode.get_mode()

            # B. 讀取影像
            frame = cam.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            display_frame = frame.copy() # 預設顯示原圖

            # C. 根據模式處理
            if current_mode == "DETECTION":
                # 1. 送圖給 AI (如果 Queue 沒滿)
                if not frame_queue.full():
                    frame_queue.put(frame)

                # 2. 嘗試取得 AI 結果 (非阻塞)
                try:
                    res_frame, plate_text = result_queue.get_nowait()
                    display_frame = res_frame # 更新為有畫框的圖
                    
                    # 3. 觸發存檔邏輯 (如果有偵測到車牌)
                    if plate_text:
                        now = time.time()
                        # 防抖動：同一台車 N 秒內不重複存
                        if (plate_text != last_plate_text) or (now - last_save_time > SAVE_COOLDOWN):
                            
                            # 讀取地磅重量
                            weight = scale.get_weight()
                            
                            # 儲存圖片證據
                            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            img_filename = f"runs/images/{timestamp_str}_{plate_text}.jpg"
                            os.makedirs("runs/images", exist_ok=True)
                            cv2.imwrite(img_filename, frame) # 存原始乾淨圖或標註圖皆可
                            
                            # 寫入資料庫 (CSV)
                            db.save_record(plate_text, weight, img_filename)
                            
                            # 更新狀態
                            last_plate_text = plate_text
                            last_save_time = now
                            print(f"✅ 紀錄完成: {plate_text} | {weight}kg")
                            
                except Empty:
                    pass # AI 還沒算完，繼續顯示上一幀或原圖

            # D. 繪製 UI 資訊
            # 顯示模式狀態
            color = (0, 255, 0) if current_mode == "DETECTION" else (0, 165, 255)
            cv2.putText(display_frame, f"Mode: {current_mode}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            # 顯示操作提示
            cv2.putText(display_frame, "ESC: Exit", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # E. 顯示畫面
            cv2.imshow("Smart LPR System", display_frame)

            # F. 鍵盤控制 (備用退出機制)
            key = cv2.waitKey(1) & 0xFF
            if key == 27: # ESC
                break

    except KeyboardInterrupt:
        print("\n[System] Interrupted by user.")
    
    finally:
        # G. 資源釋放
        print("[System] Shutting down...")
        stop_event.set()     # 通知 AI 執行緒停止
        ai_thread.join()     # 等待 AI 執行緒結束
        cam.release()        # 關相機
        scale.close()        # 關地磅
        
        if btn_mode: btn_mode.cleanup()
        if btn_power: btn_power.cleanup()
        
        # AI 系統內部釋放 (TensorRT 顯存)
        ai_system.cleanup() 
        
        cv2.destroyAllWindows()
        print("[System] Goodbye.")

if __name__ == "__main__":
    main()
