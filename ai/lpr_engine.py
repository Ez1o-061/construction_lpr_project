
from ultralytics import YOLO
import cv2
from paddleocr import PaddleOCR
import gc
import atexit

from ocrprocess import OCRProcess

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


        try:
            # YOLO 偵測
            results = self._detector.predict(source=frame, verbose=False)
            
            for result in results:
                for box in result.boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box)
                    
                    # 畫框 (偵測到車牌)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # 擷取車牌區域進行 OCR
                    roi = frame[y1:y2+1, x1:x2+1]

                    #進行ocr
                    if roi.size > 0:
                        # 呼叫 OCR
                        ocr_result = self._ocr.run(roi)
            
            return frame

        except Exception as e:
            return frame # 發生錯誤仍回傳原圖，保證系統不中斷

 
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


#出錯直接raise


if __name__ =="__main__":
    from  camera import Camera
    cam = Camera()
    test = Detect_License_Plate("./model/license_plate_y11x_best.pt")
    while(1):
        frame = cam.get()
        if frame is not None:
            temp = test.run(frame)
        cv2.imshow("test",temp)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            cam.cleanup()
            break

    




