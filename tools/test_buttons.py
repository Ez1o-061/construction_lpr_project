import time
from modules.button import Button
from modules.button_power import ButtonPower

# 假設接腳：模式按鈕接 Pin 24, 電源按鈕接 Pin 25
# 請根據你實際的接線修改這裡的 Pin 號碼
MODE_PIN = 24
POWER_PIN = 25

def test():
    print("--- 開始按鈕測試 (按 Ctrl+C 結束) ---")
    try:
        btn_mode = Button(pin=MODE_PIN)
        btn_power = ButtonPower(pin=POWER_PIN)
        
        while True:
            # 持續監聽狀態
            m = btn_mode.get_mode()
            p = btn_power.get_mode()
            
            # 為了避免洗頻，只有狀態改變時才 print 比較好
            # 但測試階段我們先簡單每秒印一次狀態
            print(f"Current Status -> Mode: {m} | Power: {p}")
            
            if p == "POWER_OFF":
                print("!!! 偵測到關機訊號 !!!")
                # 測試腳本不真的關機，只重置狀態方便繼續測
                # 實際使用時這裡就會 break 出去執行 shutdown
                btn_power._mode = "POWER_ON" 
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n測試結束，清理資源...")
        btn_mode.cleanup()
        btn_power.cleanup()

if __name__ == "__main__":
    test()
