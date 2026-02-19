import Jetson.GPIO as GPIO
import cv2
import os
from button import Button
from detect_license_plate import Detect_License_Plate

from mainprocess import MainProcess

import threading
from multiprocessing import Process,Queue 
import queue  # 這樣才能正確捕捉 queue.Full
import time

def listen_button(btn, q):
    while(1):
        listen = btn.get_push()

        if listen:
            try: 
                q.put(True,timeout = 1) 
                btn.know() #確定資訊確實傳出去
            except queue.Full:
                continue
        time.sleep(0.1)

    

if __name__ == "__main__":

    q = Queue(maxsize=5)

    #創建一個process執行偵測車牌
    main_process = MainProcess(q,"laptop.engine")

    #license和show功能切換的按鈕
    license_show_switch = Button(15) 

    #write_infromation = WriteInformation() #還未完成

    th_btn = threading.Thread(listen_button, args = (target = license_show_switch, q))
    th_btn.start()

    while(1):
        #這裡做錯誤處理，判斷要不要重啟物件等





    



