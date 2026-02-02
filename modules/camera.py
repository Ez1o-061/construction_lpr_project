import cv2

class CameraDriver:
    def __init__(self, camera_id=0, width=1280, height=720):
        """
        初始化 USB 攝影機驅動
        Args:
            camera_id (int): 攝影機 ID，通常為 0
            width (int): 解析度寬度
            height (int): 解析度高度
        """
        self.camera_id = camera_id
        self.cap = cv2.VideoCapture(camera_id)
        
        # 設定解析度
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if not self.cap.isOpened():
            print(f"[Camera] Error: Could not open camera ID {camera_id}")
            self.is_running = False
        else:
            print(f"[Camera] Initialized successfully (ID: {camera_id})")
            self.is_running = True

    def get_frame(self):
        """
        擷取單張影像
        Returns:
            frame: OpenCV 影像物件，若讀取失敗回傳 None
        """
        if self.is_running:
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                print("[Camera] Warning: Failed to retrieve frame")
        return None

    def release(self):
        """釋放攝影機資源"""
        if self.cap.isOpened():
            self.cap.release()
            print("[Camera] Resource released")

if __name__ == "__main__":
    # 單元測試
    cam = CameraDriver()
    if cam.is_running:
        print("[Test] Press 'q' to exit")
        while True:
            frame = cam.get_frame()
            if frame is not None:
                cv2.imshow("Camera Test", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cam.release()
        cv2.destroyAllWindows()
