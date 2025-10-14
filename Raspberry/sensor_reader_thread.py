# SensorReaderThread.py – Handles serial communication for 3 pressure sensors
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from collections import Counter
import time

class SensorReaderThread(QThread):
    data_received = pyqtSignal(int, float)    # sensor_id, pressure in mmHg
    calibration_finished = pyqtSignal(list)   # offsets for GUI, optional
    request_calibration = pyqtSignal()        # GUI to Thread

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, parent=None):
        super().__init__(parent)
        self.running = True
        self.port = port
        self.baudrate = baudrate
        self.partial_data = {i: {'low': None, 'high': None} for i in range(3)}

        # Sensor calibration
        self.VREF = 3.3
        self.sensor1_OFFSET = 118
        self.sensor2_OFFSET = 135
        self.sensor3_OFFSET = 123

        # Calibration data
        self.sensor1_k = (330 - 0) / (932 - 118)
        self.sensor2_k = (330 - 0) / (920 - 135)
        self.sensor3_k = (330 - 0) / (914 - 123)

        # Thread-safe flag for calibration request
        self.calibration_requested = False

        # Connect signal to slot internally (for external .emit())
        self.request_calibration.connect(self.start_offset_calibration)

    def run(self):
        import serial
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        except Exception as e:
            print(f"Serial error: {e}")
            return

        while self.running:
            # Calibration request handling
            if self.calibration_requested:
                self._perform_calibration()
                self.calibration_requested = False
                continue  # Resume main loop for normal acquisition

            # Standard data acquisition
            if self.ser.in_waiting:
                byte = self.ser.read(1)[0]
                flag = byte & 0b00000001
                sensor_id = (byte >> 1) & 0b00000011
                pressure_bits = (byte >> 3) & 0b00011111

                if flag == 0:
                    self.partial_data[sensor_id]['low'] = pressure_bits
                else:
                    self.partial_data[sensor_id]['high'] = pressure_bits

                if (self.partial_data[sensor_id]['low'] is not None and self.partial_data[sensor_id]['high'] is not None):
                    low = self.partial_data[sensor_id]['low']
                    high = self.partial_data[sensor_id]['high']
                    pressure_raw = (high << 5) | low

                    # Apply calibration offsets
                    if sensor_id == 0:
                        pressure_mmHg = self.sensor1_k * (pressure_raw - self.sensor1_OFFSET)
                    elif sensor_id == 1:
                        pressure_mmHg = self.sensor2_k * (pressure_raw - self.sensor2_OFFSET)
                    elif sensor_id == 2:
                        pressure_mmHg = self.sensor3_k * (pressure_raw - self.sensor3_OFFSET)

                    self.data_received.emit(sensor_id, pressure_mmHg)

                    # Reset for next sample
                    self.partial_data[sensor_id]['low'] = None
                    self.partial_data[sensor_id]['high'] = None

        self.ser.close()

    @pyqtSlot()
    def start_offset_calibration(self):
        """Sets flag so calibration will be performed in run()."""
        print("[SensorReaderThread] Calibration requested.")
        self.calibration_requested = True

    def _perform_calibration(self):
        print("[SensorReaderThread] Collecting zero offset samples...")
        num_samples = 2000
        sample_data = {0: [], 1: [], 2: []}
        started = time.time()

        # Collect samples
        while any(len(samples) < num_samples for samples in sample_data.values()) and self.running:
            if self.ser.in_waiting:
                byte = self.ser.read(1)[0]
                flag = byte & 0b00000001
                sensor_id = (byte >> 1) & 0b00000011
                pressure_bits = (byte >> 3) & 0b00011111

                if flag == 0:
                    self.partial_data[sensor_id]['low'] = pressure_bits
                else:
                    self.partial_data[sensor_id]['high'] = pressure_bits

                if (self.partial_data[sensor_id]['low'] is not None and
                    self.partial_data[sensor_id]['high'] is not None and
                    len(sample_data[sensor_id]) < num_samples):

                    low = self.partial_data[sensor_id]['low']
                    high = self.partial_data[sensor_id]['high']
                    pressure_raw = (high << 5) | low

                    sample_data[sensor_id].append(pressure_raw)

                    self.partial_data[sensor_id]['low'] = None
                    self.partial_data[sensor_id]['high'] = None

            if time.time() - started > 10:  # Timeout after 10s
                print("[SensorReaderThread] Calibration timeout.")
                break

        # Find mode for each sensor's samples
        offsets = []
        for sid in (0, 1, 2):
            samples = sample_data[sid]
            if samples:
                try:
                    mode_val, _ = Counter(samples).most_common(1)[0]
                except Exception:
                    import numpy as np
                    mode_val = int(np.median(samples))
            else:
                print(f"[SensorReaderThread] Warning: no data for sensor {sid}.")
                mode_val = 0
            offsets.append(mode_val)

        # Set new offsets
        self.sensor1_OFFSET, self.sensor2_OFFSET, self.sensor3_OFFSET = offsets

        print(f"[SensorReaderThread] Calibration complete. New zero offsets: {offsets}")
        self.calibration_finished.emit(offsets)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()
