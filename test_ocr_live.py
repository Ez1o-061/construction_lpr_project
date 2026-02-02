import cv2
from paddleocr import PaddleOCR
import time

# 初始化 OCR (不跑 YOLO，單純跑 OCR)
print("👀 載入 OCR 引擎中...")
ocr = PaddleOCR(use_textline_orientation=True, lang='en', show_log=False)

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

print("✅ OCR 測試啟動！請拿有文字的東西（車牌、課本、手機畫面）給鏡頭看")
print("按 'q' 離開")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 為了效能，我們每 5 幀才辨識一次，不然畫面會卡
    # 這裡我們直接跑，卡頓是正常的，因為 CPU 滿載
    try:
        results = ocr.ocr(frame, cls=False)
        
        # 如果有抓到字
        if results and results[0]:
            for line in results[0]:
                # line 的結構: [[x,y], ('TEXT', conf)]
                box = line[0]
                text, conf = line[1]
                
                # 印在終端機
                print(f"抓到: {text} (信心度: {conf:.2f})")
                
                # 畫在畫面上 (把座標轉成整數)
                pt1 = (int(box[0][0]), int(box[0][1]))
                cv2.putText(frame, text, pt1, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    except Exception as e:
        print(f"Error: {e}")

    cv2.imshow('Live OCR Test', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
