from multiprocessing import Process,Queue 
import cv2
import queue
import time
import threading

from camera import Camera
from detect_license_plate import  Detect_License_Plate


class MainProcess(Process):
    def __init__(self, 
                 q,
                 model_path,  
                text_detection_model_dir = None, 
                text_recognition_model_dir = None
                ):
        super().__init__()
        self.model_path = model_path

        self._text_det = text_detection_model_dir
        self._text_rec = text_recognition_model_dir

        self._status = "detect"  # "detect" / "show"

        self._q = q #Queue，儲存按鍵是否被按下

    def run(self):

        self._init_components()

        ListenButtonTh = threading.thread(target = self._ListenMainButton,deamon = True)
        ListenButtonTh.start()
        try:
            while(1):
                frame = self._cam.get()
                if not frame:
                    print("[MainProcess] : don't read img continue")
                    continue
                if self._status == "detect":       #地磅未完成
                    self._detect.run(frame)
                
                elif self._status == "show":
                    cv2.imshow("Jetson Camera", frame)
                    cv2.waitKey(1)
        except Exception as e:
            self.cleanup()


    def _init_components(self):
        # 真正跑在子進程的記憶體空間裡
        print("[MainProcess]: 正在子進程中安全初始化硬體與 AI 引擎...")
        self._cam = Camera()
        self._detect = Detect_License_Plate(self.model_path, self._text_det, self._text_rec)

    def _ListenMainButton(self): #用來監聽main傳輸的button訊號
                                 #判斷要是show還是detect模式
        while(1):
            try:
                # 嘗試直接拿，拿不到立刻噴 Error 跳到 except，完全不阻塞
                temp = self._q.get(block=False) 
                
                if temp:
                    self._status = "show" if self._status == "detect" else "detect"
                    print(f"[MainProcess]: 狀態已切換為: {self._status}")
            
            except queue.Empty:
                pass
           
            time.sleep(0.05)
    def cleanup(self):
        self._cam.cleanup()


if __name__ == "__main__":
    

            
            
        



    
