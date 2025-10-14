from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
import pyqtgraph as pg
import random
import numpy as np
from functools import partial

class LivePlotter(QWidget):
    stats_updated = pyqtSignal(str, dict)  # name, {systole, diastole, mean}

    def __init__(self, parent_widget=None):
        if parent_widget is not None:
            if hasattr(parent_widget, "centralWidget") and parent_widget.centralWidget():
                parent = parent_widget.centralWidget()
            else:
                parent = parent_widget
        else:
            parent = None

        super().__init__(parent)
        self.setGeometry(40, 130, 700, 430)

        self.setStyleSheet("background-color: black; color: white;")
        self.layout = QVBoxLayout(self)
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setBackground('k')
        self.layout.addWidget(self.plot_widget)

        # Toggle smoothing here
        self.use_smoothing = True

        self.channels = {
            "LVP": {'color': 'green', 'timer': QTimer(), 'data': [0]*200},
            "AOP": {'color': 'red', 'timer': QTimer(), 'data': [0]*200},
            "LAP": {'color': 'yellow', 'timer': QTimer(), 'data': [0]*200},
            "FLOW": {'color': 'cyan', 'timer': QTimer(), 'data': [0]*200},
        }

        self.x = list(range(200))
        self.curves = {}

        for name, config in self.channels.items():
            plot = self.plot_widget.addPlot()
            plot.setYRange(0, 180 if name != "FLOW" else 20)
            plot.getAxis('bottom').setTicks([])  # Hide x-axis numbers
            plot.showGrid(x=True, y=True, alpha=0.08)
            plot.getAxis('left').setPen(pg.mkPen(color='w', width=1))
            plot.getAxis('left').setTextPen('white')
            plot.getAxis('left').setStyle(showValues=True)

            curve = plot.plot(pen=pg.mkPen(config['color'], width=2, antialias=True))
            self.curves[name] = curve

            config['timer'].timeout.connect(partial(self.update_plot, name))
            config['timer'].start(50)

            self.plot_widget.nextRow()

    def update_plot(self, name):
        config = self.channels[name]
        new_value = random.randint(30, 140) if name != "FLOW" else random.randint(0, 15)
        config['data'] = config['data'][1:] + [new_value]

        if self.use_smoothing:
            smoothed = np.convolve(config['data'], np.ones(5)/5, mode='same')
            self.curves[name].setData(self.x, smoothed)
        else:
            self.curves[name].setData(self.x, config['data'])

        data = config['data']
        if data:
            systole = max(data)
            diastole = min(data)
            mean_val = sum(data) / len(data)
            self.stats_updated.emit(name, {
                "systole": systole,
                "diastole": diastole,
                "mean": mean_val
            })

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
