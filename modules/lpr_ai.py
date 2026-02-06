import cv2
import re
import logging
import gc
from ultralytics import YOLO
from paddleocr import PaddleOCR

# 關閉 PaddleOCR 的詳細日誌
logging.getLogger("ppocr").setLevel(logging.ERROR)

class LPRSystem:
    def __init__(self, model_path='models/best.engine'):
        print(f"[AI] 正在載入 YOLO 模型: {model_path} ...")
        # 使用 TensorRT 引擎加速
        self.detector = YOLO(model_path, task='detect')
        
        print("[AI] 正在啟動 PaddleOCR (英文模式)...")
        # 優化參數：關閉方向分類與變形校正以提升速度
        self.ocr = PaddleOCR(
            use_angle_cls=False, 
            lang='en', 
            show_log=False,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )

    def validate_license_plate(self, raw_text):
        """
        過濾雜訊，回傳符合台灣車牌格式的字串與規則名稱
        Returns: (is_valid, clean_text, rule_name)
        """
        if not raw_text: return False, "", ""
        
        # 1. 強制轉大寫並移除所有非英數符號
        clean_text = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
        if not clean_text: return False, "", ""

        # 2. 定義台灣常見車牌格式與名稱 (整合同事的標註邏輯)
        rules = [
            (r'^[0-9]{3}[A-Z]{2}$', "舊式汽車 (123-AB)"),
            (r'^[A-Z]{3}[0-9]{4}$', "新式汽車 (ABC-1234)"),
            (r'^[A-Z]{3}[0-9]{3}$', "舊式機車 (ABC-123)"),
            (r'^[0-9]{2}[A-Z]{1}[0-9]{1}$', "特殊/電動 (22-A-1)"),
            (r'^[A-Z]{1,2}[0-9]{3,4}$', "寬鬆規則/計程車"),
            (r'^[A-Z]{2}[0-9]{3,4}$', "營業車"),
            (r'^[A-Z]{3}[0-9]{4}$', "租賃車")
        ]

        # 3. 比對規則
        for pattern, label in rules:
            if re.match(pattern, clean_text):
                return True, clean_text, label
        
        return False, clean_text, "Unknown"

    def draw_labeled_box(self, frame, x1, y1, x2, y2, text, label_type, conf):
        """
        繪製標註框 (移植自 combine.py 的 draw_results)
        """
        h, w, _ = frame.shape
        color = (0, 255, 0) # 綠色
        text_color = (255, 255, 255) # 白色
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2

        # 1. 確保座標安全
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        # 2. 準備顯示文字
        display_str = f"{text} ({conf:.2f})"
        
        # 3. 計算文字區塊大小
        (text_w, text_h), baseline = cv2.getTextSize(display_str, font, font_scale, 1)
        
        # 4. 畫主框
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        # 5. 畫文字背景 (處理邊界問題)
        # 如果上方空間不夠，就把文字畫在框內
        if y1 - text_h - 10 < 0:
            rect_y1 = y1
            rect_y2 = y1 + text_h + 10
            text_pos_y = y1 + text_h + 5
        else:
            rect_y1 = y1 - text_h - 10
            rect_y2 = y1
            text_pos_y = y1 - 5

        rect_x2 = min(x1 + text_w, w)
        
        # 實心背景
        cv2.rectangle(frame, (x1, rect_y1), (rect_x2, rect_y2), color, -1)
        # 文字
        cv2.putText(frame, display_str, (x1, text_pos_y), font, font_scale, text_color, 1, cv2.LINE_AA)

    def process_frame(self, frame):
        """
        輸入: 影像
        輸出: 畫好框的圖, 最佳車牌文字
        """
        # YOLO 推論
        results = self.detector(frame, verbose=False, conf=0.4, imgsz=640)
        
        annotated_frame = frame.copy()
        best_plate_text = None
        best_conf = 0.0

        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 取得座標
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # 裁切車牌圖片 (ROI)
                h, w, _ = frame.shape
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                plate_roi = frame[y1:y2, x1:x2]
                if plate_roi.size == 0: continue

                # 送進 OCR 辨識
                ocr_results = self.ocr.ocr(plate_roi, cls=False)
                
                if ocr_results and ocr_results[0]:
                    # 抓出信心度最高的結果
                    res = max(ocr_results[0], key=lambda x: x[1][1])
                    raw_text = res[1][0]
                    ocr_conf = res[1][1]
                    
                    # 驗證格式
                    is_valid, clean_text, rule_label = self.validate_license_plate(raw_text)
                    
                    if is_valid:
                        # 使用新的繪圖函式
                        self.draw_labeled_box(annotated_frame, x1, y1, x2, y2, clean_text, rule_label, ocr_conf)
                        
                        # 紀錄最佳結果 (取信心度最高者)
                        if ocr_conf > best_conf:
                            best_conf = ocr_conf
                            best_plate_text = clean_text
                    else:
                        # (可選) 繪製辨識失敗的框，用紅色表示
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 1)

        return annotated_frame, best_plate_text

    def cleanup(self):
        """
        釋放資源 (移植自 detect_license_plate.py)
        """
        print("[AI] 正在釋放模型資源...")
        try:
            if hasattr(self, 'detector'):
                del self.detector
            if hasattr(self, 'ocr'):
                del self.ocr
            gc.collect() # 強制垃圾回收
            print("[AI] 資源釋放完畢")
        except Exception as e:
            print(f"[AI] 釋放失敗: {e}")

if __name__ == "__main__":
    # 單元測試
    lpr = LPRSystem()
    print("[Test] 測試 cleanup...")
    lpr.cleanup()
