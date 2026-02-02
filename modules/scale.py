import serial
import time
import random

class ScaleDriver:
    def __init__(self, port='/dev/ttyUSB0', baud=9600, simulate=True):
        """
        地磅驅動程式
        :param port: 地磅的 USB 孔位 (Linux 通常是 /dev/ttyUSB0)
        :param baud: 傳輸速率 (常見為 9600 或 2400)
        :param simulate: 模擬模式開關 (True=產生假數據, False=讀取真實硬體)
        """
        self.port = port
        self.baud = baud
        self.simulate = simulate
        self.ser = None
        
        # 如果不是模擬模式，嘗試連線
        if not self.simulate:
            try:
                self.ser = serial.Serial(self.port, self.baud, timeout=1)
                print(f"✅ [Scale] 地磅硬體已連線: {self.port}")
            except serial.SerialException as e:
                print(f"⚠️ [Scale] 無法連接地磅 ({e})")
                print("🔄 自動切換為 [模擬模式]")
                self.simulate = True

    def get_weight(self):
        """
        讀取重量
        :return: 重量數值 (float)，單位 kg
        """
        # --- 模式 A: 模擬模式 (沒接線時用) ---
        if self.simulate:
            # 模擬一台卡車開上來的過程：數值會浮動
            base_weight = 3500  # 假設卡車 3.5 噸
            noise = random.uniform(-10, 10) # 模擬感測器雜訊
            return round(base_weight + noise, 1)

        # --- 模式 B: 真實硬體模式 ---
        if self.ser and self.ser.in_waiting:
            try:
                # 1. 讀取一行資料 (byte -> string)
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                # 2. 解析數據 (Parsing)
                # 假設地磅格式是 "ST,GS,+  3500kg" 或純數字 "3500"
                # 這裡使用簡單的過濾：只留下數字和小數點
                import re
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                
                if numbers:
                    # 通常取抓到的第一個數字當作重量
                    return float(numbers[0])
                    
            except Exception as e:
                print(f"❌ [Scale] 數據解析錯誤: {e}")
        
        return 0.0

    def close(self):
        if self.ser:
            self.ser.close()
            print("🔴 [Scale] 連線已關閉")

# --- 單元測試區塊 ---
if __name__ == "__main__":
    print("🔧 進入地磅模組測試...")
    # 這裡預設 simulate=True，因為你現在沒硬體
    driver = ScaleDriver(simulate=True)
    
    try:
        while True:
            w = driver.get_weight()
            # 印出像儀表板一樣的動態效果
            print(f"\r⚖️ 當前重量: {w:.1f} kg", end="")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n🛑 測試結束")
    finally:
        driver.close()
