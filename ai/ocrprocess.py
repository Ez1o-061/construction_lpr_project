from paddleocr import PaddleOCR
import os
import re

class OCRProcess: #回傳陣列，所有通過測試可能是正確的車牌
    def __init__(self, 
                 text_detection_model_dir = None, 
                 text_recognition_model_dir = None
                 ):
        """
        初始化 OCR，若不傳入路徑則使用預設模型
        """

        common_config = {
            "use_angle_cls": True,             # 建議開啟，處理文字倒置
            "use_gpu": True,                   # Jetson Nano 必開
            "lang": "en",                      # 語言設定
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
        }

        try:

            #  判斷是否使用自定義模型路徑
            if  text_detection_model_dir and  text_recognition_model_dir:
                print(f"[OCRProcess] 使用自定義模型路徑: \n{text_detection_model_dir}")
                print(f"{text_detection_model_dir}")
                self._ocr = PaddleOCR(
                    det_model_dir = text_detection_model_dir, 
                    rec_model_dir = text_recognition_model_dir, 
                    **common_config
                )
            else:
                print("[OCRProcess] 使用 PaddleOCR 預設模型")
                self._ocr = PaddleOCR(**common_config)
        except Exception as e:
            print("[OCRProcess]: 模型載入失敗")

    """
    過濾雜訊，回傳符合台灣車牌格式的字串與規則名稱
    Returns: (is_valid, clean_text, rule_name)
    """
    def _validate_license_plate(self, raw_text):

        if not raw_text or str(raw_text).strip() == "": 
            return False, "", ""

        # 1. 先轉大寫並去除所有非英數符號 (包含空格與連字號)
        clean_text = re.sub(r'[^A-Z0-9]', '', raw_text.upper())

        # 2. 處理 I -> 1 與 O -> 0 的轉換
        clean_text = clean_text.replace('I', '1').replace('O', '0')

        if not clean_text: 
            return False, "", "不含任何英數內容"
    
        # 2. 定義台灣常見車牌格式與名稱 (整合同事的標註邏輯)
        rules = [
            # --- 汽車類 ---
            (r'^[0-9]{3}[A-Z]{2}$', "舊式汽車 (123-AB)"),
            (r'^[A-Z]{2}[0-9]{3}$', "舊式汽車 (AB-123)"), # 補上 AB-123 格式
            (r'^[A-Z]{3}[0-9]{4}$', "新式汽車/租賃車 (ABC-1234)"),

            # --- 租賃車與特殊編碼 (如 393-R5) ---
            (r'^[0-9]{3}[A-Z]{1}[0-9]{1}$', "舊式租賃/身障車 (123-A-1)"), # 393-R-5 變體
            (r'^[0-9]{3}[A-Z]{2}$', "舊式租賃車 (123-RR)"), 
            (r'^[A-Z]{1}[0-9]{1}[A-Z]{1}[0-9]{2}$', "身障車 (A1-B2)"), # 補上身障專用車
            (r'^[0-9]{3}[A-Z]{2}$', "舊式汽車 (123-AB)"), 
            (r'^[0-9]{2}[A-Z]{2}$', "舊式汽車 (12-AB)"), # 極早期

            # --- 機車類 ---
            (r'^[A-Z]{3}[0-9]{3}$', "舊式重機/普通機車 (ABC-123)"),
            (r'^[0-9]{3}[A-Z]{3}$', "舊式機車反向 (123-ABC)"), # 補上機車反向編碼
            (r'^[A-Z]{2}[0-9]{2}$', "舊式輕型機車 (AB-12)"),
            (r'^[A-Z]{3}[0-9]{4}$', "新式機車 (ABC-1234)"),

            # --- 電動車與特殊格式 ---
            (r'^[0-9]{2}[A-Z]{1}[0-9]{1}$', "電動車/特殊格式 (22-A-1)"),
            (r'^[E]{1}[A-Z]{1}[0-9]{4}$', "電動汽車 (EA-1234)"), # 補上 E 開頭電動車
            (r'^[0-9]{4}[A-Z]{2}$', "電動機車 (1234-AB)"), # 補上電動機車 (如 1234-EM)

            # --- 營業車/計程車 ---
            (r'^[A-Z]{2}[0-9]{3,4}$', "營業/計程車 (AB-1234)"),
            (r'^[0-9]{3}[A-Z]{2}$', "營業車 (123-AB)"),
        ]

        # 3. 比對規則
        for pattern, label in rules:
            if re.match(pattern, clean_text):
                return True, clean_text, label
    
        return False, clean_text, "Unknown"

    def run(self, frame):
        """
        執行辨識的方法
        """
        result = self._ocr.ocr(frame, cls=True)

        store_plate = []
        if result and result[0]:
            for line in result[0]:
                # line[1][0] 就是辨識出的文字字串
        	text = line[1][0] 
        	unfail, plate, _ = self._validate_license_plate(text)
        	if unfail:
            	    store_plate.append(plate)
		
		# [修正] 必須把裝有車牌的陣列回傳出去！
        	return store_plate
# 使用範例
if __name__ == "__main__":
    # 情況 A：使用預設
    my_ocr = OCRProcess()
    

    # 情況 B：使用自定義路徑
'''
    my_ocr = OCRProcess(
        det_dir="/home/jetson/models/det", 
        rec_dir="/home/jetson/models/rec"
    )
'''
