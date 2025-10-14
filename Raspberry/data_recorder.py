
# RecorderThread.py 
# logs pressure data to CSV: timestamp, LVP, AOP, LAP

from PyQt5.QtCore import QThread
import queue
import time

class RecorderThread(QThread):
    def __init__(self, filename=None, parent=None):
        super().__init__(parent)
        self.queue = queue.Queue()
        self.running = True
        self.filename = filename or f"recording_{int(time.time())}.csv"
        self.file = None
        self.latest_values = {0: None, 1: None, 2: None}
        self.last_write_time = 0

    def run(self):
        self.file = open(self.filename, "w")
        self.file.write("timestamp,LVP,AOP,LAP\n")

        while self.running or not self.queue.empty():
            try:
                sensor_id, value = self.queue.get(timeout=0.1)
                self.latest_values[sensor_id] = value

                if all(v is not None for v in self.latest_values.values()):
                    timestamp = time.time()
                    lvp = self.latest_values[0]
                    aop = self.latest_values[1]
                    lap = self.latest_values[2]
                    self.file.write(f"{timestamp:.3f},{lvp:.2f},{aop:.2f},{lap:.2f}\n")
                    self.latest_values = {0: None, 1: None, 2: None}
            except queue.Empty:
                continue

        self.file.close()

    def write_value(self, sensor_id, value):
        self.queue.put((sensor_id, value))

    def stop(self):
        self.running = False
        self.wait()
