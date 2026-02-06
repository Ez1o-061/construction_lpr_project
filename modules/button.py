import Jetson.GPIO as GPIO

class Button:
    def __init__(self, pin, default_mode="DETECTION", pull_type=GPIO.PUD_DOWN, bouncetime=300):
        """
        功能切換按鈕
        Pin 被按下時，自動在 "DETECTION" 與 "CAMERA_ONLY" 模式間切換
        """
        self.pin = pin
        self._mode = default_mode
        
        # 設定 GPIO 模式 (BCM 編號)
        # 注意: 若主程式已設定過 setmode，這裡重複設定通常無害，但確保模組獨立性
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=pull_type)

        # 判斷觸發邊緣 (Edge)
        if pull_type == GPIO.PUD_DOWN:
            edge = GPIO.RISING  # 下拉電阻 -> 按下時變高電位
        else:
            edge = GPIO.FALLING # 上拉電阻 -> 按下時變低電位

        # 註冊事件偵測
        try:
            GPIO.add_event_detect(self.pin, edge, callback=self._button_callback, bouncetime=bouncetime)
            print(f"[Button] Initialized on Pin {pin} (Mode Switch)")
        except Exception as e:
            print(f"[Button] Init Error on Pin {pin}: {e}")

    def _button_callback(self, channel):
        """內部的回呼函式，負責切換狀態"""
        if self._mode == "DETECTION":
            self._mode = "CAMERA_ONLY"
        else:
            self._mode = "DETECTION"
        print(f"[Button] Mode switched to: {self._mode}")

    def get_mode(self):
        """讓主程式讀取當前模式"""
        return self._mode
    
    def cleanup(self):
        """釋放 GPIO 資源"""
        try:
            GPIO.cleanup(self.pin)
            print(f"[Button] Pin {self.pin} cleaned up")
        except Exception as e:
            print(f"[Button] Cleanup warning: {e}")
