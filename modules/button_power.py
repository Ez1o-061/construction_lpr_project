import Jetson.GPIO as GPIO

class ButtonPower:
    def __init__(self, pin, default_mode="POWER_ON", pull_type=GPIO.PUD_DOWN, bouncetime=2000):
        """
        電源控制按鈕
        bouncetime 設長一點 (2000ms = 2秒) 避免誤觸關機
        """
        self.pin = pin
        self._mode = default_mode
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=pull_type)

        if pull_type == GPIO.PUD_DOWN:
            edge = GPIO.RISING
        else:
            edge = GPIO.FALLING

        try:
            GPIO.add_event_detect(self.pin, edge, callback=self._button_callback, bouncetime=bouncetime)
            print(f"[Power] Initialized on Pin {pin}")
        except Exception as e:
            print(f"[Power] Init Error on Pin {pin}: {e}")

    def _button_callback(self, channel):
        """按下後切換為 POWER_OFF，主程式偵測到後會執行關機"""
        print(f"[Power] Button pressed! Initiating shutdown sequence...")
        self._mode = "POWER_OFF"

    def get_mode(self):
        return self._mode
    
    def cleanup(self):
        try:
            GPIO.cleanup(self.pin)
            print(f"[Power] Pin {self.pin} cleaned up")
        except Exception as e:
            print(f"[Power] Cleanup warning: {e}")
