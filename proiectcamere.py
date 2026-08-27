import cv2
import time
from threading import Thread
class CamereStream:
    def __init__(self,sursa):
        self.sursa=sursa
        self.stream=cv2.VideoCapture(sursa)
        (self.succes,self.cadru)=self.stream.read()
        self.oprit=False
        self.thread=Thread(target=self._actualizeaza,args=())
        self.thread.daemon=True
        self.thread.start()
    def _actualizeaza(self):
        esecuri=0
        while not self.oprit:
            if not self.stream.isOpened():
                self.stream.release()
                time.sleep(2)
                self.stream=cv2.VideoCapture(self.sursa)
                continue
            succes,cadru=self.stream.read()
            if not succes:
                esecuri+=1
                time.sleep(0.1)
                if esecuri>=10:
                    self.stream.release()
                    time.sleep(2)
                    self.stream=cv2.VideoCapture(self.sursa)
                    esecuri=0
                continue
            esecuri=0
            self.succes=succes
            self.cadru=cadru.copy()
    def citeste_cadru(self):
        return self.cadru.copy() if self.cadru is not None else None
    def opreste(self):
        self.oprit=True
        if self.thread.is_alive():
            self.thread.join(timeout=0.1)
        self.stream.release()