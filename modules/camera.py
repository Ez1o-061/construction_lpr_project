import cv2
import threading
from queue import Queue, Empty,Full
import atexit

class Camera:
    def __init__(self, width=1280, height=720,src=0):

        self._cap = cv2.VideoCapture(src)

        if not self._cap.isOpened():
            print(f"[Camera] Error: Could not open camera ID {src}")
            raise RuntimeError("[Camera]: can't open camera")
        else:
            print(f"[Camera] Initialized successfully (ID: {src})")
        
        # 設定解析度
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # 註冊自己的 cleanup
        atexit.register(self._InterCleanup)

        self._new_frame = None

        self._lock = threading.Lock() 

        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True
        )
        self._thread.start()

    # ========================
    # private: thread loop
    # ========================
    def _loop(self):
        try: 
            while not self._stop_event.is_set():
                ret, frame = self._cap.read()
                if not ret:
                    print("[Camera]:Camera read failed continue")
                else:
                    with self._lock:
                        self._new_frame = frame
		    time.sleep(0.01)
        except Exception as e:
            print(f"[Camera]: {e}")
            

    # ========================
    # public API
    # ========================
    def get(self):
        with self._lock:
            return self._new_frame


    def _InterCleanup(self): #強制退出
        if self._cap.isOpened():
            self._cap.release()
        print("[Camera] 成功釋放")

    def cleanup(self): #使用者退出
        """
        請求停止 camera thread
        等待釋放資源
        """
        self._stop_event.set()
        self._thread.join()


if __name__ == "__main__" :
    test_cm = Camera()
    while(1):
        frame = test_cm.get()
        if frame is not None: 
            cv2.imshow("test", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            test_cm.cleanup()
            cv2.destroyAllWindows()
            break
        

#優化 加入sleep釋放cpu資源
#如果cam創建失敗會直接raise
