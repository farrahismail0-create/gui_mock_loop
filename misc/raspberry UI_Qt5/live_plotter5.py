from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
import pyqtgraph as pg
import numpy as np
from functools import partial

class LivePlotter(QWidget):
    stats_updated = pyqtSignal(str, dict)

    def __init__(self, parent_widget=None):
        super().__init__(parent_widget.centralWidget() if parent_widget and hasattr(parent_widget, "centralWidget") else parent_widget)
        self.setGeometry(40, 130, 700, 430)
        self.setStyleSheet("background-color: black; color: white;")

        self.use_smoothing = True
        self.external_labels = {}

        self.layout = QVBoxLayout(self)
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setBackground('k')
        self.layout.addWidget(self.plot_widget)

        self.ordered_names = ["LVP", "AOP", "LAP", "FLOW"]
        self.channels = {}
        self.curves = {}

        for name in self.ordered_names:
            color = {"LVP": "green", "AOP": "red", "LAP": "yellow", "FLOW": "cyan"}[name]
            timer = QTimer()
            data = [0] * 200

            plot = self.plot_widget.addPlot()
            plot.setYRange(0, 180 if name != "FLOW" else 20)
            plot.setMouseEnabled(x=False, y=False)
            plot.getAxis('bottom').setTicks([])
            plot.showGrid(x=True, y=True, alpha=0.08)
            plot.getAxis('left').setPen(pg.mkPen(color='w', width=1))
            plot.getAxis('left').setTextPen('white')
            plot.getAxis('left').setStyle(showValues=True)

            curve = plot.plot(pen=pg.mkPen(color, width=2, antialias=True))

            self.channels[name] = {
                'color': color,
                'timer': timer,
                'data': data,
                'plot': plot,
                'visible': True
            }

            self.curves[name] = curve
            timer.timeout.connect(partial(self.update_plot, name))
            timer.start(50)
            self.plot_widget.nextRow()

        self.x = list(range(200))

    def register_labels(self, label_map):
        self.external_labels = label_map

    def update_plot(self, name):
        config = self.channels[name]
        new_value = np.random.randint(30, 140) if name != "FLOW" else np.random.randint(0, 15)
        config['data'] = config['data'][1:] + [new_value]

        ydata = np.convolve(config['data'], np.ones(5) / 5, mode='same') if self.use_smoothing else config['data']
        self.curves[name].setData(self.x, ydata)

        if len(ydata) > 0:
            systole = int(max(ydata))
            diastole = int(min(ydata))
            mean_val = sum(ydata) / len(ydata)

            self.stats_updated.emit(name, {
                "systole": systole,
                "diastole": diastole,
                "mean": mean_val
            })

            if name in self.external_labels:
                label = self.external_labels[name]
                if name == "FLOW":
                    label.setText(f"{name}\n{mean_val:.1f}")
                else:
                    label.setText(f"{name}\n{systole}/{diastole}")
                label.setStyleSheet(f"color: {config['color']};")

    def toggle_channel(self, name):
        config = self.channels[name]
        config['visible'] = not config['visible']

        if config['visible']:
            config['timer'].start(50)
            if name in self.external_labels:
                self.external_labels[name].setStyleSheet(f"color: {config['color']}; font-weight: bold; background-color: transparent;")
        else:
            config['timer'].stop()
            if name in self.external_labels:
                self.external_labels[name].setStyleSheet(f"color: gray; font-weight: bold; background-color: transparent;")

        self.rebuild_layout()


    def rebuild_layout(self):
        self.plot_widget.clear()
        for name in self.ordered_names:
            config = self.channels[name]
            if config['visible']:
                self.plot_widget.addItem(config['plot'])
                self.plot_widget.nextRow()

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
