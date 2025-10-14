
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
import pyqtgraph as pg

class LivePlotter(QWidget):
    stats_updated = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setGeometry(40, 130, 700, 430)

        self.layout = QVBoxLayout(self)
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.plot_widget)

        self.channels = {
            "LVP": {'color': 'r', 'data': [0]*2000},
            "AOP": {'color': 'g', 'data': [0]*2000},
            "LAP": {'color': 'b', 'data': [0]*2000},
            "FLOW": {'color': 'y', 'data': [0]*2000},
        }

        self.x = list(range(2000))
        self.curves = {}

        for name, config in self.channels.items():
            plot = self.plot_widget.addPlot(title=name)
            plot.setYRange(0, 180 if name != "FLOW" else 20)
            curve = plot.plot(pen=pg.mkPen(config['color'], width=2))
            self.curves[name] = curve
            self.plot_widget.nextRow()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_plot)
        self.timer.start(50)

    def receive_data(self, name, value):
        if name in self.channels:
            self.channels[name]['data'].append(value)
            if len(self.channels[name]['data']) > 200:
                self.channels[name]['data'].pop(0)

    def refresh_plot(self):
        for name, config in self.channels.items():
            data = config['data']
            self.curves[name].setData(self.x[-len(data):], data)
            if data:
                systole = max(data)
                diastole = min(data)
                mean_val = sum(data) / len(data)
                self.stats_updated.emit(name, {
                    "systole": systole,
                    "diastole": diastole,
                    "mean": mean_val
                })
