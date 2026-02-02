import serial
import time
import random
import re

class ScaleDriver:
    def __init__(self, port='/dev/ttyUSB0', baud=9600, simulate=True):
        """
        地磅訊號驅動程式
        Args:
            port (str): Serial Port 路徑 (例如 /dev/ttyUSB0)
            baud (int): 傳輸速率
            simulate (bool): 是否啟用模擬模式
        """
        self.port = port
        self.baud = baud
        self.simulate = simulate
        self.ser = None
        
        if not self.simulate:
            try:
                self.ser = serial.Serial(self.port, self.baud, timeout=1)
                print(f"[Scale] Hardware connected at {self.port}")
            except serial.SerialException as e:
                print(f"[Scale] Connection failed ({e}), switching to simulation mode")
                self.simulate = True

    def get_weight(self):
        """
        讀取當前重量
        Returns:
            float: 重量 (kg)，若讀取失敗回傳 0.0
        """
        # --- 模擬模式 ---
        if self.simulate:
            base = 3500.0
            noise = random.uniform(-5.0, 5.0)
            return round(base + noise, 1)

        # --- 真實硬體模式 ---
        if self.ser and self.ser.in_waiting:
            try:
                # 讀取並解碼，忽略解碼錯誤
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                # 使用正則表達式 (Regex) 提取數字 (支援整數與浮點數)
                # 例如: "ST,GS,+ 3500kg" -> ['3500']
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                
                if numbers:
                    return float(numbers[0])
            except Exception as e:
                print(f"[Scale] Parse error: {e}")
        
        return 0.0

    def close(self):
        """關閉連線"""
        if self.ser:
            self.ser.close()
            print("[Scale] Connection closed")

# --- 單元測試區塊 ---
if __name__ == "__main__":
    print("[Scale] Running module self-check (Simulation)...")
    driver = ScaleDriver(simulate=True)
    try:
        for _ in range(5):
            w = driver.get_weight()
            print(f"[Scale] Readout: {w} kg")
            time.sleep(0.5)
        print("[Scale] Test passed.")
    except KeyboardInterrupt:
        print("[Scale] Test interrupted.")
    finally:
        driver.close()
