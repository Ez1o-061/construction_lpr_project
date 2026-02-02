import cv2
import logging
import numpy as np
import urllib.request
from ultralytics import YOLO
from paddleocr import PaddleOCR

# 抑制 PaddleOCR 的除錯日誌
logging.getLogger("ppocr").setLevel(logging.ERROR)

class LPRSystem:
    def __init__(self, yolo_path='yolov8n.pt'):
        """
        初始化車牌辨識系統 (YOLOv8 + PaddleOCR)
        Args:
            yolo_path (str): YOLO 模型路徑
        """
        print("[AI] Loading YOLO model (GPU)...")
        self.detector = YOLO(yolo_path)
        
        print("[AI] Loading PaddleOCR engine (CPU)...")
        self.ocr = PaddleOCR(use_textline_orientation=True, lang='en')
        
        # 設定目標類別 (2=car, 5=bus, 7=truck)
        self.target_classes = [2, 5, 7]

    def process_frame(self, frame):
        """
        處理影像進行車輛偵測與車牌辨識
        Returns:
            tuple: (標記後的影像, 辨識到的文字或None)
        """
        # 1. YOLO 物件偵測
        results = self.detector(frame, verbose=False, conf=0.5)
        detections = results[0]
        
        has_vehicle = False
        plate_text = None
        
        # 檢查是否偵測到車輛
        for box in detections.boxes:
            if int(box.cls[0]) in self.target_classes:
                has_vehicle = True
                break
        
        # 2. 若有車，執行 OCR
        if has_vehicle:
            # 針對全圖進行 OCR
            ocr_results = self.ocr.ocr(frame, cls=False)
            
            if ocr_results and ocr_results[0]:
                # 取出信心度最高的結果
                best_match = max(ocr_results[0], key=lambda x: x[1][1])
                text, conf = best_match[1]
                
                # 過濾短雜訊 (車牌通常長度 > 4)
                if len(text) > 4:
                    plate_text = text

        # 繪製 YOLO 偵測框
        annotated_frame = detections.plot()
        
        return annotated_frame, plate_text

# --- 測試區塊 ---
if __name__ == "__main__":
    print("[Test] Running AI module self-check...")
    
    # 下載測試圖 (巴士)
    url = 'https://ultralytics.com/images/bus.jpg'
    print(f"[Test] Downloading image: {url}")
    try:
        req = urllib.request.urlopen(url)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        
        # 初始化系統
        lpr = LPRSystem()
        
        # 執行辨識
        result_img, text = lpr.process_frame(img)
        print(f"[Test] Detection Result: {text}")
        print("[Test] Module is working correctly.")
        
        # 顯示結果 (按 q 離開)
        cv2.imshow("AI Module Test", result_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"[Test] Error: {e}")
