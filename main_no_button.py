import cv2
import threading
import time
import os
from queue import Queue, Full, Empty
from datetime import datetime

# 引入核心模組 (不含按鈕)
from modules.camera import CameraDriver
from modules.lpr_ai import LPRSystem
from modules.scale import ScaleDriver
from modules.database import DatabaseManager

# --- 設定區 ---
CAMERA_ID = 0
SAVE_COOLDOWN = 5.0  # 同一台車幾秒內不重複存檔

def main():
    print("========================================")
    print("   無按鈕測試模式 (Keyboard Control)    ")
    print("   [M] 切換模式 (偵測/純相機)           ")
    print("   [ESC] 離開程式                       ")
    print("========================================")

    # 1. 初始化系統模組
    print("[System] Initializing modules...")
    
    # 硬體 (模擬地磅開啟)
    cam = CameraDriver(camera_id=CAMERA_ID)
    scale = ScaleDriver(simulate=True) 
    
    # 軟體 (AI & DB)
    # 請確認你的 models 資料夾內有 best.engine
    ai_system = LPRSystem() 
    db = DatabaseManager()

    # 2. 建立多執行緒通訊機制
    frame_queue = Queue(maxsize=1)  # 存放待辨識影像
    result_queue = Queue(maxsize=1) # 存放辨識結果
    stop_event = threading.Event()  # 用來安全停止

    # ---------------------------
    # AI 工作執行緒 (Worker Thread)
    # ---------------------------
    def ai_worker():
        print("[AI Worker] Started.")
        while not stop_event.is_set():
            try:
                # 等待影像輸入 (timeout 讓執行緒有機會檢查 stop_event)
                frame = frame_queue.get(timeout=0.1)
                
                # 執行辨識
                annotated_frame, best_text = ai_system.process_frame(frame)
                
                # 將結果送回主執行緒 (丟棄舊資料以保持即時性)
                if result_queue.full():
                    try: result_queue.get_nowait()
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
    print("[System] Ready.")
    
    # 狀態變數
    current_mode = "DETECTION" # 預設開啟偵測
    last_save_time = 0
    last_plate_text = ""

    try:
        while True:
            # A. 讀取影像
            frame = cam.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            display_frame = frame.copy()

            # B. 根據模式處理
            if current_mode == "DETECTION":
                # 1. 送圖給 AI
                if not frame_queue.full():
                    frame_queue.put(frame)

                # 2. 嘗試取得 AI 結果
                try:
                    res_frame, plate_text = result_queue.get_nowait()
                    display_frame = res_frame # 顯示畫好框的圖
                    
                    # 3. 觸發存檔邏輯 (如果有偵測到車牌)
                    if plate_text:
                        now = time.time()
                        # 防抖動：同一車牌 N 秒內不重複存
                        if (plate_text != last_plate_text) or (now - last_save_time > SAVE_COOLDOWN):
                            
                            # 讀取地磅重量
                            weight = scale.get_weight()
                            
                            # 儲存圖片
                            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            img_filename = f"runs/images/{timestamp_str}_{plate_text}.jpg"
                            os.makedirs("runs/images", exist_ok=True)
                            cv2.imwrite(img_filename, frame) 
                            
                            # 寫入資料庫
                            db.save_record(plate_text, weight, img_filename)
                            
                            # 更新狀態
                            last_plate_text = plate_text
                            last_save_time = now
                            print(f"✅ [SAVED] {plate_text} | {weight}kg")
                            
                except Empty:
                    pass # AI 還在算，顯示上一張或原圖

            # C. 繪製 UI 資訊
            # 根據模式改變文字顏色
            color = (0, 255, 0) if current_mode == "DETECTION" else (0, 165, 255)
            cv2.putText(display_frame, f"Mode: {current_mode}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            # 顯示鍵盤操作提示
            cv2.putText(display_frame, "[M] Toggle Mode | [ESC] Exit", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # D. 顯示畫面
            cv2.imshow("Smart LPR System (Test)", display_frame)

            # E. 鍵盤控制邏輯
            key = cv2.waitKey(1) & 0xFF
            if key == 27: # ESC 鍵
                break
            elif key == ord('m') or key == ord('M'): # M 鍵切換模式
                if current_mode == "DETECTION":
                    current_mode = "CAMERA_ONLY"
                else:
                    current_mode = "DETECTION"
                print(f"[Input] Mode switched to: {current_mode}")

    except KeyboardInterrupt:
        print("\n[System] Interrupted by user.")
    
    finally:
        # F. 資源釋放
        print("[System] Shutting down...")
        stop_event.set()     # 通知 AI 停止
        ai_thread.join()     # 等待 AI 結束
        cam.release()
        scale.close()
        ai_system.cleanup() 
        cv2.destroyAllWindows()
        print("[System] Goodbye.")

if __name__ == "__main__":
    main()
