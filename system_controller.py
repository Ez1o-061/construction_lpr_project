from multiprocessing import Process, Queue 
import cv2
import queue
import time
import threading
import os

# 引入所有硬體與系統模組
from modules.camera import Camera
from modules.database import DatabaseManager
from modules.scale import ScaleDriver

# 引入 AI 模組
from ai.lpr_engine import Detect_License_Plate 

class SystemController(Process):
    def __init__(self, q, model_path, text_det=None, text_rec=None):
        super().__init__()
        self.model_path = model_path
        self._text_det = text_det
        self._text_rec = text_rec
        self._q = q 
        self._status = "detect" 
        
        # 簡單的防抖變數，避免 Terminal 被同一個車牌洗頻，也避免狂存相同的照片
        self.last_plate = ""
        self.last_detect_time = 0

    def _init_components(self):
        """在子進程中安全初始化所有硬體與模組"""
        print("[SystemController] 正在子進程初始化所有硬體與模組...")
        
        # 1. 啟動相機
        self._cam = Camera()
        
        # 2. 載入 AI 引擎 (YOLO + PaddleOCR)
        self._detect = Detect_License_Plate(self.model_path, self._text_det, self._text_rec)
        
        # 3. 初始化資料庫 (封裝了存圖與寫入 CSV 功能)
        self._db = DatabaseManager(base_dir="runs", enable_scale_img=False)
        
        # 4. 初始化地磅 (Demo 階段開啟 simulate=True 模擬假重量)
        self._scale = ScaleDriver(simulate=True)

    def run(self):
        # 啟動所有資源
        self._init_components() 
        
        # 啟動按鈕監聽執行緒
        ListenButtonTh = threading.Thread(target=self._ListenMainButton, daemon=True)
        ListenButtonTh.start()

        try:
            while True:
                # 取得影像幀
                frame = self._cam.get()
                if frame is None:
                    time.sleep(0.01)
                    continue

                display_frame = frame.copy()

                # ==========================================
                # 模式 A: 偵測模式 (核心業務邏輯)
                # ==========================================
                if self._status == "detect":
                    # 1. 執行 AI 辨識
                    processed_frame, plate_text = self._detect.run(frame)
                    display_frame = processed_frame

                    # 2. 整合資料流：抓重量、交給資料庫統一存圖與寫入
                    if plate_text:
                        now = time.time()
                        
                        # 防抖機制：同一個車牌 3 秒內不重複紀錄
                        if (plate_text != self.last_plate) or (now - self.last_detect_time > 3.0):
                            
                            # A. 抓取地磅重量
                            weight = self._scale.get_weight()
                            
                            # B. 將畫面與文字直接丟給 Database 處理 (高度封裝)
                            self._db.save_record(
                                plate_status="辨識成功", 
                                plate=plate_text, 
                                frame=display_frame, # 直接傳遞影像陣列，讓資料庫模組去存
                                scale_status="穩定", 
                                weight=weight
                            )

                            # 更新防抖狀態
                            self.last_plate = plate_text
                            self.last_detect_time = now

                # ==========================================
                # 模式 B: 純顯示模式 (僅供監視)
                # ==========================================
                elif self._status == "show":
                    cv2.putText(display_frame, "VIEW ONLY MODE", (10, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

                # ==========================================
                # 畫面顯示與離開判定
                # ==========================================
                cv2.imshow("Smart LPR System", display_frame)
                if cv2.waitKey(1) & 0xFF == 27: # 按下 ESC 鍵離開
                    break
                    
        except Exception as e:
            print(f"[SystemController] 執行階段發生未預期錯誤: {e}")
        finally:
            self.cleanup()

    def _ListenMainButton(self):
        """獨立執行緒：監聽主程式傳來的按鈕切換訊號"""
        while True:
            try:
                if self._q.get(block=False):
                    self._status = "show" if self._status == "detect" else "detect"
                    print(f"[SystemController] 狀態已切換為: {self._status}")
            except queue.Empty:
                pass
            time.sleep(0.05) # 避免 CPU 空轉

    def cleanup(self):
        """優雅關機：釋放所有硬體與系統資源"""
        print("[SystemController] 準備關閉系統與釋放資源...")
        try:
            self._cam.cleanup()
            self._scale.close()
            cv2.destroyAllWindows()
            print("[SystemController] 資源釋放完畢。")
        except Exception as e:
            print(f"[SystemController] 釋放資源時發生錯誤: {e}")
