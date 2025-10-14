from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
import pyqtgraph as pg
import numpy as np
from functools import partial

class LivePlotter(QWidget):
    stats_updated = pyqtSignal(str, dict)

    def __init__(self, parent_widget=None, use_real_data=False):
        super().__init__(parent_widget.centralWidget() if parent_widget and hasattr(parent_widget, "centralWidget") else parent_widget)
        self.setGeometry(40, 130, 700, 430)
        self.setStyleSheet("background-color: black; color: white;")

        self.use_real_data = True
        self.use_smoothing = True
        self.external_labels = {}

        self.layout = QVBoxLayout(self)
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setBackground('k')
        self.layout.addWidget(self.plot_widget)

        self.ordered_names = ["LVP", "AOP", "LAP", "FLOW"]
        self.channels = {}
        self.curves = {}

        self.x = list(range(200))

        for name in self.ordered_names:
            color = {"LVP": "green", "AOP": "red", "LAP": "yellow", "FLOW": "cyan"}[name]
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
                'data': data,
                'plot': plot,
                'curve': curve,
                'visible': True
            }

            self.curves[name] = curve
            self.plot_widget.nextRow()

        if self.use_real_data:
            self.timer = QTimer()
            self.timer.timeout.connect(self.refresh_plot)
            self.timer.start(50)
        else:
            for name in self.ordered_names:
                timer = QTimer()
                timer.timeout.connect(partial(self.update_plot, name))
                timer.start(50)
                self.channels[name]['timer'] = timer

    def register_labels(self, label_map):
        self.external_labels = label_map

    def receive_data(self, name, value):
        if name in self.channels:
            self.channels[name]['data'].append(value)
            if len(self.channels[name]['data']) > 200:
                self.channels[name]['data'].pop(0)

    def refresh_plot(self):
        for name in self.ordered_names:
            if self.channels[name]['visible']:
                self.update_curve(name)

    def update_plot(self, name):
        config = self.channels[name]
        new_value = np.random.randint(30, 140) if name != "FLOW" else np.random.randint(0, 15)
        config['data'] = config['data'][1:] + [new_value]
        self.update_curve(name)

    def update_curve(self, name):
        config = self.channels[name]
        data = config['data']
        ydata = np.convolve(data, np.ones(5) / 5, mode='same') if self.use_smoothing else data
        config['curve'].setData(self.x[-len(ydata):], ydata)

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
                label.setStyleSheet(f"color: {config['color']}; font-weight: bold; background-color: transparent;")

    def toggle_channel(self, name):
        config = self.channels[name]
        config['visible'] = not config['visible']

        if not self.use_real_data:
            if config['visible']:
                config['timer'].start(50)
            else:
                config['timer'].stop()

        if name in self.external_labels:
            color = config['color'] if config['visible'] else "gray"
            self.external_labels[name].setStyleSheet(f"color: {color}; font-weight: bold; background-color: transparent;")

        self.rebuild_layout()

    def rebuild_layout(self):
        self.plot_widget.clear()
        for name in self.ordered_names:
            config = self.channels[name]
            if config['visible']:
                self.plot_widget.addItem(config['plot'])
                self.plot_widget.nextRow()

    def pause_all(self):
        if not self.use_real_data:
            for name in self.ordered_names:
                self.channels[name]['timer'].stop()

    def resume_all(self):
        if not self.use_real_data:
            for name in self.ordered_names:
                self.channels[name]['timer'].start(50)
