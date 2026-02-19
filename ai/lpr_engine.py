from ultralytics import YOLO
import cv2
import gc
import atexit

from .ocrprocess import OCRProcess

class Detect_License_Plate:

    def __init__(
            self, 
            model_path, 
            text_detection_model_dir = None, 
            text_recognition_model_dir = None 
            ):

        #兩個ai模型
        self._ocr = None
        self._detector = None

        print("[Detect_License_Plate]: 正在加載模型 ocr and yolo")
        try:

            self._ocr = OCRProcess(text_detection_model_dir,
                                   text_recognition_model_dir
                                   )
            print("[Detect_License_Plate]: ocr模型成功載入")
            

            self._detector = YOLO(model_path)
            print("[Detect_License_Plate]: yolo模型成功載入")

        except Exception as e:
            print(f"[Detect_License_Plate]: 模型初始化失敗: {e}")

        # 註冊cleanup
        atexit.register(self.cleanup)

    def run(self, frame):
        # === 修改 1：新增變數儲存最終車牌文字 ===
        best_plate = None 

        try:
            # YOLO 偵測
            results = self._detector.predict(source=frame, verbose=False)
            
            for result in results:
                for box in result.boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box)
                    
                    # 擷取車牌區域進行 OCR
                    roi = frame[y1:y2+1, x1:x2+1]

                    # 進行 ocr
                    if roi.size > 0:
                        # 呼叫 OCR，同事的 ocrprocess 會回傳一個裝有合法車牌的 list
                        ocr_results = self._ocr.run(roi)
                        
                        # === 修改 2：取出車牌並畫上文字與框線 ===
                        if ocr_results and len(ocr_results) > 0:
                            best_plate = ocr_results[0] # 抓取第一筆通過正則驗證的車牌
                            
                            # 畫框 (偵測到車牌)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            # 畫上辨識出的車牌文字
                            cv2.putText(frame, best_plate, (x1, y1 - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # === 修改 3：同時回傳影像與車牌文字 ===
            return frame, best_plate

        except Exception as e:
            print(f"[Detect_License_Plate] 執行錯誤: {e}")
            # 發生錯誤仍回傳原圖與 None，保證系統不中斷
            return frame, None 

 
    def cleanup(self):
        print("[ALPR] 啟動資源釋放程序...")
        try:
            # 顯式銷毀大型物件以釋放 TensorRT 與 Paddle 佔用的顯存
            if hasattr(self, '_detector'):
                del self._detector
            if hasattr(self, '_ocr'):
                del self._ocr
            
            # 強制執行垃圾回收
            gc.collect()
            print("[ALPR] 資源釋放完畢")
        except Exception as e:
            print(f"[ALPR] 釋放資源時發生錯誤: {e}")

# 單元測試區塊
if __name__ =="__main__":
    import sys
    import os
    # 將上層目錄加入 path 以便測試時能找到 modules.camera
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from modules.camera import Camera
    
    cam = Camera()
    test = Detect_License_Plate("../models/best.engine") # 記得換成你的測試模型路徑
    
    while(1):
        frame = cam.get()
        if frame is not None:
            # 使用兩個變數接收
            temp_frame, text = test.run(frame)
            if text:
                print(f"[Test] 偵測到車牌: {text}")
            cv2.imshow("test", temp_frame)
            
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            cam.cleanup()
            break
