import cv2
import time
import os
import logging
from datetime import datetime

# 匯入自定義模組
from modules.camera import CameraDriver
from modules.lpr_ai import LPRSystem
from modules.scale import ScaleDriver
from modules.database import DatabaseManager

class ConstructionSiteSystem:
    def __init__(self):
        """
        初始化工地自動化管理系統
        負責整合相機、AI 辨識、地磅與資料庫模組。
        """
        print("=== Initializing Construction Site System ===")
        
        # 1. 系統參數設定 (Configuration)
        self.save_dir = "runs/records"
        self.save_cooldown = 5.0  # 相同車輛存檔冷卻時間 (秒)
        self.last_save_time = 0
        self.last_plate = ""
        
        # 確保儲存目錄存在
        os.makedirs(self.save_dir, exist_ok=True)

        # 2. 初始化各個模組
        try:
            self.cam = CameraDriver(camera_id=0)
            self.ai = LPRSystem()
            self.scale = ScaleDriver(simulate=True) # 開發階段預設開啟模擬
            self.db = DatabaseManager()
            print("[System] All modules initialized successfully.")
        except Exception as e:
            print(f"[System] Critical Error during initialization: {e}")
            exit(1)

    def run(self):
        """
        系統主迴圈
        流程: 影像擷取 -> AI 辨識 -> 地磅讀取 -> 邏輯判斷 -> 存檔 -> 顯示
        """
        print("[System] System started. Press 'q' to exit.")
        
        try:
            while True:
                # A. 影像擷取
                frame = self.cam.get_frame()
                if frame is None:
                    print("[System] Video stream lost.")
                    break

                # B. AI 推論 (偵測車輛與車牌)
                annotated_frame, plate_text = self.ai.process_frame(frame)
                
                # C. 讀取地磅重量
                weight = self.scale.get_weight()

                # D. 顯示資訊介面 (UI Overlay)
                self._draw_ui(annotated_frame, weight, plate_text)

                # E. 存檔邏輯 (自動化紀錄)
                # 條件: 1.有偵測到車牌 2.冷卻時間已過 (避免重複寫入)
                current_time = time.time()
                if plate_text:
                    if (current_time - self.last_save_time > self.save_cooldown) or (plate_text != self.last_plate):
                        self.save_event(plate_text, weight, frame)
                        self.last_save_time = current_time
                        self.last_plate = plate_text

                # F. 畫面更新
                cv2.imshow("Site Monitor System", annotated_frame)

                # 按 'q' 離開
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("[System] Shutdown signal received.")
                    break
                    
        except KeyboardInterrupt:
            print("[System] Interrupted by user.")
        except Exception as e:
            print(f"[System] Runtime Error: {e}")
        finally:
            self.close()

    def _draw_ui(self, frame, weight, plate_text):
        """繪製螢幕資訊"""
        # 顯示重量
        weight_text = f"Weight: {weight:.1f} kg"
        cv2.putText(frame, weight_text, (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # 若有偵測到車牌，顯示車牌號碼
        if plate_text:
            plate_info = f"Plate: {plate_text}"
            cv2.putText(frame, plate_info, (20, 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    def save_event(self, plate, weight, frame):
        """
        觸發存檔流程: 存圖 + 寫入資料庫
        """
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}_{plate}.jpg"
        filepath = os.path.join(self.save_dir, filename)
        
        # 1. 儲存圖片
        cv2.imwrite(filepath, frame)
        
        # 2. 寫入資料庫
        self.db.save_record(plate, weight, filepath)
        
        print(f"[Event] Logged: Plate={plate}, Weight={weight}kg, File={filename}")

    def close(self):
        """安全釋放所有資源"""
        print("=== Shutting Down System ===")
        if hasattr(self, 'cam'): self.cam.release()
        if hasattr(self, 'scale'): self.scale.close()
        if hasattr(self, 'db'): self.db.close()
        cv2.destroyAllWindows()
        print("[System] Goodbye.")

if __name__ == "__main__":
    app = ConstructionSiteSystem()
    app.run()
