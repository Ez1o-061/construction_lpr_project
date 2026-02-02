import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR
import time
import logging

# 設定 Log 不顯示太多雜訊
logging.getLogger("ppocr").setLevel(logging.ERROR)

class LPRSystem:
    def __init__(self, yolo_path='yolov8n.pt', use_gpu_ocr=False):
        """
        初始化 LPR 系統
        :param yolo_path: YOLO 模型路徑
        :param use_gpu_ocr: PaddleOCR 是否使用 GPU (Orin Nano 建議 False)
        """
        print("🧠 [AI] 正在載入 YOLO 模型 (GPU)...")
        # 你的環境 PyTorch 支援 GPU，所以這裡會自動用 GPU
        self.detector = YOLO(yolo_path)
        
        print(f"👀 [AI] 正在載入 PaddleOCR (GPU={use_gpu_ocr})...")
        # lang='en' 辨識數字與英文較準
        self.ocr = PaddleOCR(use_textline_orientation=True, lang='en')
        
        # 設定要偵測的類別 (COCO dataset: 2=car, 5=bus, 7=truck)
        self.target_classes = [2, 5, 7]

    def process_frame(self, frame):
        """
        處理單張影像：偵測車輛 -> (若有車) -> 辨識車牌
        回傳: (annotated_frame, plate_text)
        """
        # 1. YOLO 偵測
        results = self.detector(frame, verbose=False, conf=0.5)
        detections = results[0]
        
        has_vehicle = False
        plate_text = None
        
        # 過濾偵測到的物件
        for box in detections.boxes:
            cls_id = int(box.cls[0])
            if cls_id in self.target_classes:
                has_vehicle = True
                break
        
        # 2. 若有車，進行 OCR
        if has_vehicle:
            # 這裡為了效能，你可以只裁切 bbox 出來做 OCR，這裡先示範全圖
            ocr_results = self.ocr.ocr(frame, cls=False)
            
            if ocr_results and ocr_results[0]:
                # 找出信心度最高的文字區塊
                best_match = max(ocr_results[0], key=lambda x: x[1][1])
                text, conf = best_match[1]
                
                # 簡單過濾：車牌通常大於 4 碼
                if len(text) > 4:
                    plate_text = text

        # 繪製 YOLO 偵測框
        annotated_frame = detections.plot()
        
        # 若有辨識到文字，畫在左上角
        if plate_text:
            cv2.putText(annotated_frame, f"Plate: {plate_text}", 
                        (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return annotated_frame, plate_text

# --- 單元測試區塊 ---
if __name__ == "__main__":
    print("🔧 進入 AI 辨識單元測試模式...")
    # 下載一張網路圖片測試
    import numpy as np
    import urllib.request
    
    lpr = LPRSystem()
    
    url = 'https://ultralytics.com/images/bus.jpg'
    print(f"📥 下載測試圖片: {url}")
    req = urllib.request.urlopen(url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv2.imdecode(arr, -1)
    
    # 執行辨識
    result_img, text = lpr.process_frame(img)
    print(f"🔍 辨識結果: {text}")
