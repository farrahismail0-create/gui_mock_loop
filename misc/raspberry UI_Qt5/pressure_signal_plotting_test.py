# Full standalone GUI: Receives data from Arduino and plots it live (Sensor 1 only, styled like a clinical monitor)

import sys
import serial
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

class LivePlotter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Plot setup
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setYRange(0, 350)  # Clinical monitor style
        self.plot_widget.setLabel('left', 'Pressure', units='mmHg')
        self.plot_widget.setLabel('bottom', '')
        self.plot_widget.getPlotItem().getAxis('bottom').setTicks([])  # Hide x-axis numbers
        self.plot_widget.showGrid(x=False, y=True)  # Optional: vertical grid only
        self.curve = self.plot_widget.plot(pen='y')

        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

        # Serial port setup
        try:
            self.ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
        except Exception as e:
            print("Could not open Port:", e)
            sys.exit(1)

        # Data buffers
        self.buffer = []
        self.buffer_size = 100
        self.partial_data = {
            0: {'low': None, 'high': None},
            1: {'low': None, 'high': None},
            2: {'low': None, 'high': None}
        }

        # Calibration constants
        self.VREF = 3.3
        self.OFFSET = 0.42
        self.measured_mmHg = 100
        self.measured_Voltage = 1.1
        self.SENSITIVITY = (self.measured_Voltage - self.OFFSET) / self.measured_mmHg

        # Timer to update plot
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)

    def update_plot(self):
        while self.ser.in_waiting:
            byte = self.ser.read(1)[0]

            flag = byte & 0b00000001
            sensor_id = (byte >> 1) & 0b00000011
            pressure_bits = (byte >> 3) & 0b00011111

            if sensor_id != 0:
                continue  # Only plot sensor 1 for now

            if flag == 0:
                self.partial_data[sensor_id]['low'] = pressure_bits
            else:
                self.partial_data[sensor_id]['high'] = pressure_bits

            if self.partial_data[sensor_id]['low'] is not None and self.partial_data[sensor_id]['high'] is not None:
                low = self.partial_data[sensor_id]['low']
                high = self.partial_data[sensor_id]['high']
                pressure_raw = (high << 5) | low

                voltage = (pressure_raw / 1023.0) * self.VREF
                pressure_mmHg = (voltage - self.OFFSET) / self.SENSITIVITY

                self.buffer.append(pressure_mmHg)
                if len(self.buffer) > self.buffer_size:
                    self.buffer.pop(0)

                self.partial_data[sensor_id]['low'] = None
                self.partial_data[sensor_id]['high'] = None

        # Update the plot with reversed x-axis (0 on right)
        x = list(range(-len(self.buffer) + 1, 1))
        self.curve.setData(x, self.buffer)

class PressureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pressure Signal Monitor')
        self.setGeometry(100, 100, 800, 600)

        self.live_plotter = LivePlotter(self)
        self.setCentralWidget(self.live_plotter)

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = PressureApp()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print("GUI Error:", e)
        sys.exit(1)
