import cv2
import re
import logging
from ultralytics import YOLO
from paddleocr import PaddleOCR

# 關閉 PaddleOCR 的囉嗦日誌
logging.getLogger("ppocr").setLevel(logging.ERROR)

class LPRSystem:
    def __init__(self, model_path='models/license_plate_y8x_best.engine'):
        print(f"[AI] 正在載入 YOLO 模型: {model_path} ...")
        # 這裡會自動使用 TensorRT 引擎加速
        self.detector = YOLO(model_path, task='detect')
        
        print("[AI] 正在啟動 PaddleOCR (英文模式)...")
        # use_angle_cls=False 可以加速，因為車牌通常是水平的
        self.ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)

    def validate_license_plate(self, raw_text):
        """
        過濾雜訊，只回傳符合台灣車牌格式的字串
        """
        if not raw_text: return False, ""
        
        # 1. 強制轉大寫並移除所有非英數符號
        clean_text = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
        
        if not clean_text: return False, ""

        # 2. 定義台灣常見車牌格式
        rules = [
            r'^[0-9]{3}[A-Z]{2}$',         # 123-AB (舊式)
            r'^[A-Z]{3}[0-9]{4}$',         # ABC-1234 (新式汽車)
            r'^[A-Z]{3}[0-9]{3}$',         # ABC-123 (舊式機車)
            r'^[0-9]{2}[A-Z]{1}[0-9]{1}$', # 22-A-1 (特殊)
            r'^[A-Z]{1,2}[0-9]{3,4}$',     # 寬鬆規則
            r'^[A-Z]{2}[0-9]{3,4}$'        # 營業車
        ]

        # 3. 比對規則
        for pattern in rules:
            if re.match(pattern, clean_text):
                return True, clean_text
        
        return False, clean_text # 雖然有字，但不像車牌

    def process_frame(self, frame):
        """
        輸入: 影像
        輸出: 畫好框的圖, 辨識到的車牌文字(如果有的話)
        """
        # YOLO 推論 (conf=0.4 過濾掉低信心度的框)
        results = self.detector(frame, verbose=False, conf=0.4, imgsz=640)
        
        annotated_frame = frame.copy()
        best_plate_text = None

        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 取得座標
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # 裁切車牌圖片 (ROI)
                h, w, _ = frame.shape
                # 確保座標不超出畫面
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                plate_roi = frame[y1:y2, x1:x2]
                
                if plate_roi.size == 0: continue

                # 送進 OCR 辨識
                ocr_results = self.ocr.ocr(plate_roi, cls=False)
                
                label_text = "Analyzing..."
                color = (0, 100, 255) # 橘色 (偵測到但未讀出)

                if ocr_results and ocr_results[0]:
                    # 抓出信心度最高的結果
                    # PaddleOCR 回傳格式: [[[[x,y],..], ('text', conf)], ...]
                    res = max(ocr_results[0], key=lambda x: x[1][1])
                    raw_text = res[1][0]
                    
                    # 驗證格式
                    is_valid, clean_text = self.validate_license_plate(raw_text)
                    
                    if is_valid:
                        label_text = clean_text
                        color = (0, 255, 0) # 綠色 (成功!)
                        best_plate_text = clean_text

                # 畫框與文字
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated_frame, label_text, (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        return annotated_frame, best_plate_text
