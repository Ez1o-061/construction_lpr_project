import cv2
import threading
import queue
import time
from modules.camera import CameraDriver
from modules.lpr_ai import LPRSystem
# 先註解掉還沒寫好的部分，確保今天能先跑起來
# from modules.scale import ScaleDriver 
# from modules.database import DatabaseManager

# 建立兩個佇列 (Queue) 用來在執行緒間傳遞資料
frame_queue = queue.Queue(maxsize=1)  # 放原始圖片
result_queue = queue.Queue(maxsize=1) # 放 AI 處理結果

def ai_worker():
    """
    這是 AI 的背景工作區，它會在後台默默一直跑
    """
    print("[Thread] AI 執行緒啟動...")
    # 載入 AI 模型 (這會花幾秒鐘)
    ai_system = LPRSystem(model_path='best.engine')
    
    while True:
        # 從佇列拿圖片
        try:
            frame = frame_queue.get(timeout=1) # 等待圖片
        except queue.Empty:
            continue

        # 進行辨識
        annotated_frame, plate_text = ai_system.process_frame(frame)
        
        # 把結果丟出去
        if result_queue.full():
            result_queue.get() # 如果滿了就丟掉舊的
        result_queue.put((annotated_frame, plate_text))

def main():
    # 1. 啟動攝影機
    cap = cv2.VideoCapture(0) # 如果是 USB 相機用 0，CSI 相機可能要用 Gstreamer 字串
    if not cap.isOpened():
        print("無法開啟攝影機！")
        return

    # 2. 啟動 AI 背景執行緒
    t = threading.Thread(target=ai_worker)
    t.daemon = True # 設定為守護執行緒，主程式關閉時它會跟著關
    t.start()

    print("[System] 系統啟動中...按 'Q' 離開")
    
    current_display = None # 目前要顯示的畫面
    last_plate = "Waiting..."

    while True:
        ret, frame = cap.read()
        if not ret: break

        # 降低解析度以提升速度 (選用)
        # frame = cv2.resize(frame, (640, 480))

        # 把最新的畫面丟給 AI (如果 AI 現在有空的話)
        if not frame_queue.full():
            frame_queue.put(frame)

        # 檢查有沒有新的 AI 結果
        if not result_queue.empty():
            current_display, detected_text = result_queue.get()
            if detected_text:
                last_plate = detected_text
                print(f"辨識到車牌: {last_plate}")

        # 如果還沒有 AI 結果，就顯示原始畫面
        final_img = current_display if current_display is not None else frame

        # 在畫面上印出最新資訊
        cv2.putText(final_img, f"Last Plate: {last_plate}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("Jetson LPR System", final_img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
