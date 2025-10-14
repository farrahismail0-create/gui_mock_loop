from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer
import pyqtgraph as pg
import random


class LivePlotter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(40, 130, 700, 430)

        self.layout = QVBoxLayout(self)
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.plot_widget)

        self.channels = {
            "LVP": {'color': 'r', 'timer': QTimer(), 'data': [0]*200},
            "AOP": {'color': 'g', 'timer': QTimer(), 'data': [0]*200},
            "LAP": {'color': 'b', 'timer': QTimer(), 'data': [0]*200},
            "FLOW": {'color': 'y', 'timer': QTimer(), 'data': [0]*200},
        }

        self.x = list(range(200))
        self.curves = {}

        for name, config in self.channels.items():
            plot = self.plot_widget.addPlot(title=name)
            plot.setYRange(0, 180 if name != "FLOW" else 20)
            curve = plot.plot(pen=pg.mkPen(config['color'], width=2))
            self.curves[name] = curve
            config['timer'].timeout.connect(lambda name=name: self.update_plot(name))
            config['timer'].start(50)
            self.plot_widget.nextRow()

    def update_plot(self, name):
        config = self.channels[name]
        config['data'] = config['data'][1:] + [random.randint(30, 140) if name != "FLOW" else random.randint(0, 15)]
        self.curves[name].setData(self.x, config['data'])

    def pause(self, name):
        self.channels[name]['timer'].stop()

    def resume(self, name):
        self.channels[name]['timer'].start(50)

    def pause_all(self):
        for name in self.channels:
            self.pause(name)

    def resume_all(self):
        for name in self.channels:
            self.resume(name)
