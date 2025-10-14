
# GUI_plotter.py – Multi-Sensor Live Plotting with nano Serial Input (dev mode)

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class SerialReaderThread(QThread):
    data_received = pyqtSignal(int, float)

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, parent=None):
        super().__init__(parent)
        self.running = True
        self.port = port
        self.baudrate = baudrate
        self.partial_data = {i: {'low': None, 'high': None} for i in range(3)}
        self.VREF = 3.3
        self.OFFSET = 0.42
        self.measured_mmHg = 100
        self.measured_Voltage = 1.1
        self.SENSITIVITY = (self.measured_Voltage - self.OFFSET) / self.measured_mmHg

    def run(self):
        import serial
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        except Exception as e:
            print(f"Error opening serial port {self.port}: {e}")
            return

        while self.running:
            if self.ser.in_waiting:
                byte = self.ser.read(1)[0]
                flag = byte & 0b00000001
                sensor_id = (byte >> 1) & 0b00000011
                pressure_bits = (byte >> 3) & 0b00011111

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

                    self.data_received.emit(sensor_id, pressure_mmHg)

                    self.partial_data[sensor_id]['low'] = None
                    self.partial_data[sensor_id]['high'] = None

        self.ser.close()

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class LivePlotter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot_widget = pg.GraphicsLayoutWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.plot_widget)

        self.channels = {
            "LVP": {'color': 'r', 'data': [], 'max': 180},
            "AOP": {'color': 'g', 'data': [], 'max': 180},
            "LAP": {'color': 'b', 'data': [], 'max': 180},
        }

        self.buffer_size = 200
        self.curves = {}

        for name, config in self.channels.items():
            plot = self.plot_widget.addPlot(title=name)
            plot.setYRange(0, config['max'])
            plot.getAxis('bottom').setTicks([])
            plot.showGrid(x=False, y=True)
            curve = plot.plot(pen=pg.mkPen(config['color'], width=2))
            self.curves[name] = curve
            self.plot_widget.nextRow()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_plot)
        self.timer.start(50)

    def receive_data(self, sensor_name, value):
        channel = self.channels.get(sensor_name)
        if channel is not None:
            channel['data'].append(value)
            if len(channel['data']) > self.buffer_size:
                channel['data'].pop(0)

    def refresh_plot(self):
        for name, config in self.channels.items():
            ydata = config['data']
            xdata = list(range(-len(ydata)+1, 1))
            self.curves[name].setData(xdata, ydata)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GUI Plotter – Real Sensor Input")
        self.setGeometry(100, 100, 800, 600)

        self.plotter = LivePlotter(self)
        self.setCentralWidget(self.plotter)

        self.serial_thread = SerialReaderThread(port="/dev/ttyUSB0")
        self.serial_thread.data_received.connect(self.handle_data)
        self.serial_thread.start()

    def handle_data(self, sensor_id, value):
        if sensor_id == 0:
            self.plotter.receive_data("LVP", value)
        elif sensor_id == 1:
            self.plotter.receive_data("AOP", value)
        elif sensor_id == 2:
            self.plotter.receive_data("LAP", value)

    def closeEvent(self, event):
        self.serial_thread.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
