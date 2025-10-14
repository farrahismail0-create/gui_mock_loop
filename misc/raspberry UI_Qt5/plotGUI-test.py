import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from live_plotter2 import LivePlotter
#from live_plotter import LivePlotter

class PressureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pressure Signal Monitor')
        self.setGeometry(100, 100, 800, 600)

        # Create the LivePlotter and set it as the central widget
        self.live_plotter = LivePlotter(self)
        self.setCentralWidget(self.live_plotter)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PressureApp()
    window.show()
    sys.exit(app.exec_())
