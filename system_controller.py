from multiprocessing import Process, Queue 
import cv2
import queue
import time
import threading

# 僅引入相機與 AI 模組，尊重同事的架構要求
from modules.camera import Camera
from ai.lpr_engine import Detect_License_Plate 

class SystemController(Process):
    def __init__(self, q, model_path, text_det=None, text_rec=None):
        super().__init__()
        self.model_path = model_path
        self._text_det = text_det
        self._text_rec = text_rec
        self._q = q 
        self._status = "detect" 
        
        # 簡單的防抖變數，避免 Terminal 被同一個車牌洗頻
        self.last_plate = ""
        self.last_detect_time = 0

    def _init_components(self):
        """在子進程中安全初始化硬體相機與 AI 引擎"""
        print("[SystemController] 正在子進程初始化 Camera 與 AI...")
        self._cam = Camera()
        self._detect = Detect_License_Plate(self.model_path, self._text_det, self._text_rec)

    def run(self):
        self._init_components() 
        
        # 啟動按鈕監聽 (沿用同事邏輯)
        ListenButtonTh = threading.Thread(target=self._ListenMainButton, daemon=True)
        ListenButtonTh.start()

        try:
            while True:
                frame = self._cam.get()
                if frame is None:
                    time.sleep(0.01)
                    continue

                display_frame = frame.copy()

                # --- 模式 A: 偵測模式 ---
                if self._status == "detect":
                    # 1. 執行 AI (接收 第二步修改的 圖片 + 文字)
                    processed_frame, plate_text = self._detect.run(frame)
                    display_frame = processed_frame

                    # 2. 驗證資料流 (先不存資料庫，單純 Print)
                    if plate_text:
                        now = time.time()
                        if (plate_text != self.last_plate) or (now - self.last_detect_time > 3.0):
                            print(f"\n[AI Sub-process] 成功捕獲車牌: {plate_text} (準備傳回主程式...)")
                            self.last_plate = plate_text
                            self.last_detect_time = now

                # --- 模式 B: 純顯示模式 ---
                elif self._status == "show":
                    cv2.putText(display_frame, "VIEW ONLY MODE", (10, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

                # 顯示畫面
                cv2.imshow("Smart LPR System", display_frame)
                if cv2.waitKey(1) & 0xFF == 27: # ESC 鍵離開
                    break
                    
        except Exception as e:
            print(f"[SystemController] 執行階段發生錯誤: {e}")
        finally:
            self.cleanup()

    def _ListenMainButton(self):
        """監聽主程式傳來的按鈕訊號"""
        while True:
            try:
                if self._q.get(block=False):
                    self._status = "show" if self._status == "detect" else "detect"
                    print(f"[SystemController] 狀態已切換為: {self._status}")
            except queue.Empty:
                pass
            time.sleep(0.05)

    def cleanup(self):
        print("[SystemController] 關閉相機與視窗...")
        self._cam.cleanup()
        cv2.destroyAllWindows()
