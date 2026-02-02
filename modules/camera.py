import cv2
import time

class CameraDriver:
    def __init__(self, camera_id=0, width=1280, height=720):
        """
        初始化攝影機
        :param camera_id: 攝影機 ID (通常是 0)
        :param width: 設定解析度寬
        :param height: 設定解析度高
        """
        self.camera_id = camera_id
        self.cap = cv2.VideoCapture(camera_id)
        
        # 設定解析度 (C270 支援 720p)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if not self.cap.isOpened():
            print(f"❌ [Camera] 無法開啟攝影機 ID: {camera_id}")
            self.is_running = False
        else:
            print(f"✅ [Camera] 攝影機已啟動 (ID: {camera_id})")
            self.is_running = True

    def get_frame(self):
        """讀取一張影像"""
        if self.is_running:
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                print("⚠️ [Camera] 讀取畫面失敗")
        return None

    def release(self):
        """釋放資源"""
        if self.cap.isOpened():
            self.cap.release()
            print("🔴 [Camera] 資源已釋放")

# --- 單元測試區塊 (只在此檔案被直接執行時跑) ---
if __name__ == "__main__":
    print("🔧 進入相機單元測試模式...")
    cam = CameraDriver(camera_id=0)
    
    try:
        while True:
            frame = cam.get_frame()
            if frame is not None:
                cv2.imshow("Camera Test (Press 'q' to quit)", frame)
            
            # 按 'q' 離開測試
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cam.release()
        cv2.destroyAllWindows()
