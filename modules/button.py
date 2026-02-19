import Jetson.GPIO as GPIO
import atexit

class Button:

    def __init__(self, pin, pull_type=GPIO.PUD_OFF, bouncetime=300):

        try:
            #使用者需要的資訊
            self._push = False #按鈕有沒有被按下

            #other
            self._success_set_pin = False  #按鈕有沒有被系統成功創建

            #設定按鈕pin，等參數
            self.pin = pin
            self.bouncetime = bouncetime
            self._edge = None

            #創建按鈕
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.pin, GPIO.IN, pull_up_down=pull_type)
                self._success_set_pin = True
                print("[Button] 系統創建按鈕成功")
            except Exception as e: 
                self._success_set_pin = False
                print(f"[Button] 系統創建按鈕失敗{e}")

            if pull_type == GPIO.PUD_DOWN:
                self._edge = GPIO.RISING
            elif pull_type == GPIO.PUD_OFF:
                self._edge = GPIO.FALLING
            else:
                self._edge = GPIO.FALLING

            # 註冊自己這個 pin 的 cleanup
            atexit.register(self.cleanup)

            #call back
            GPIO.add_event_detect(self.pin, self._edge, callback=self._internal_callback, bouncetime=bouncetime)

        except Exception as e:
            if self._success_set_pin:
                self.cleanup()
            print(f"button錯誤: {e}")
            raise
        
    def _internal_callback(self, self_pin): 
        self._push = True


    def cleanup(self):
        """只釋放這個物件的 pin"""
        if self._success_set_pin:
            GPIO.cleanup(self.pin)
            print(f"[Button] Pin {self.pin} 已清理")


    # 得知按鈕是否曾被按下

    def get_push(self):
        re = self._push
        return re
    
    #使用者知道按鈕被按下，就呼叫，讓狀態變沒被按下
    def know(self):
        self._push = False


if __name__=="__main__":
    test_btn = Button(18) #BCM
    while(1):
        if test_btn.get_push() :
            print("button 被按下")
            test_btn.know()
            print("已接收btn被按下")


#優化加上getMode


    
