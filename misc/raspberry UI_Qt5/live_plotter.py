from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np


class LivePlotter(QtWidgets.QWidget):
    def __init__(self, parent_widget, width=700, height=430):
        super().__init__(parent=parent_widget.centralWidget())
        self.setGeometry(40, 130, width, height)
        self.plot_layout = QtWidgets.QVBoxLayout(self)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_layout.setSpacing(10)

        self.plot_titles = ["LVP", "AOP", "LAP", "FLOW"]
        self.waveform_plots = {}
        self.curves = {}
        self.buffers = {}
        self.buffer_size = 300  # Number of data points to keep

        for title in self.plot_titles:
            plot = pg.PlotWidget()
            plot.setBackground('k')
            plot.setTitle(title, color='w', size="12pt")
            plot.showGrid(x=True, y=True)
            plot.setYRange(0, 200 if title != "FLOW" else 20)
            plot.getPlotItem().hideAxis('bottom')
            plot.getPlotItem().getAxis('left').setPen('w')

            curve = plot.plot(pen=pg.mkPen('c', width=2))
            self.plot_layout.addWidget(plot)

            self.waveform_plots[title] = plot
            self.curves[title] = curve
            self.buffers[title] = [0] * self.buffer_size

        # Timer to simulate data updates
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_waveforms)
        self.timer.start(50)  # Update every 50ms

        self.phase = 0

    def update_waveforms(self):
        """Simulate and plot new values for each signal."""
        self.phase += 0.2
        for title in self.plot_titles:
            if title == "FLOW":
                new_val = 10 + 10 * np.sin(self.phase)
            else:
                new_val = 100 + 50 * np.sin(self.phase + np.random.uniform(-0.2, 0.2))

            self.buffers[title].append(new_val)
            self.buffers[title] = self.buffers[title][-self.buffer_size:]
            self.curves[title].setData(self.buffers[title])
