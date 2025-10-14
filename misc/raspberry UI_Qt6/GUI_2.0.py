import sys
from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg
import random
import math
import numpy as np
from second_sketch import Ui_MainWindow  # Import the UI file
from modbus_controller import set_motor_speed, set_motor_target_position, stop_motor, start_motor, reset_motor_position # TODO add a ModBusController Class
#from live_plotter import LivePlotter
from live_plotter2 import LivePlotter


class ModbusThread(QtCore.QThread):
    """Thread to update motor parameters without freezing the GUI."""
    def __init__(self, frequency, stroke_volume):
        super().__init__()
        self.frequency = frequency
        self.stroke_volume = stroke_volume

    def run(self):
        """Send updated motor values to Modbus."""
        try:
            print(f"TESTING: ModbusThread started with Frequency={self.frequency}, Stroke={self.stroke_volume}")  # Debug message
            set_motor_speed(self.frequency, self.stroke_volume)
            set_motor_target_position(self.frequency, self.stroke_volume)
        except Exception as e:
            print(f"Modbus Error: {e}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

                # Apply dark theme stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
                font-size: 16px;
            }
            QPushButton {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #5c5c5c;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #505357;
            }
            QPushButton:pressed {
                background-color: #606366;
            }
            QLabel {
                color: #f0f0f0;
            }
            QStackedWidget, QFrame {
                background-color: #2b2b2b;
            }
        """)

        # Set initial values  (should be read from Modbus on startup)
        # These value should be read from starting when first starting the GUI
        self.heart_rate = 60  # BPM (10 - 120, steps of 5)
        self.stroke_volume = 1.5  # cm (0.5 - 3, steps of 0.1)
        self.resistance = 50  # % (0 - 100, steps of 5) 

        # Timers
        self.hr_timer = QtCore.QTimer()
        self.hr_timer.setSingleShot(True)
        self.hr_timer.timeout.connect(lambda: self.ui.hrStackedWidget.setCurrentIndex(1))

        self.sv_timer = QtCore.QTimer()
        self.sv_timer.setSingleShot(True)
        self.sv_timer.timeout.connect(lambda: self.ui.svStackedWidget.setCurrentIndex(1))

        self.res_timer = QtCore.QTimer()
        self.res_timer.setSingleShot(True)
        self.res_timer.timeout.connect(lambda: self.ui.resStackedWidget.setCurrentIndex(0))

        # Long press timer
        self.hold_timer = QtCore.QTimer()
        self.hold_timer.timeout.connect(self.long_press_adjust)

        self.hold_param = None
        self.hold_step = 0
        self.hold_speed = 400  # Initial delay before increasing speed

        #
        self.plotter = LivePlotter(self)

        # Track current state of the RESET/START button
        self.is_start_mode = True

        self.ui.resetButton.setText("START")
        self.ui.resetButton.setStyleSheet("background-color: green; color: white; font-size: 20px;")
        self.ui.stopButton.setStyleSheet("background-color: red; color: black; font-size: 20px;")


        #STOP and RESET/START BUTTONs
        self.ui.stopButton.clicked.connect(self.stop_motor_function)
        self.ui.resetButton.clicked.connect(self.toggle_start_reset)
        #self.ui.resetButton.clicked.connect(self.reset_motor_function)

        # Connect value display buttons to switch to adjustment mode
        self.ui.pushButton.clicked.connect(lambda: self.show_adjustment(self.ui.hrStackedWidget, self.hr_timer, 0))
        self.ui.pushButton_2.clicked.connect(lambda: self.show_adjustment(self.ui.svStackedWidget, self.sv_timer, 0))
        self.ui.btnResistance.clicked.connect(lambda: self.show_adjustment(self.ui.resStackedWidget, self.res_timer, 1))

        # Connect + and - buttons to adjust values (long press)
        self.ui.btnHRincrease.pressed.connect(lambda: self.start_long_press("HR", 5))
        self.ui.btnHRdecrease.pressed.connect(lambda: self.start_long_press("HR", -5))
        self.ui.btnSVincrease.pressed.connect(lambda: self.start_long_press("SV", 0.1))
        self.ui.btnSVdecrease.pressed.connect(lambda: self.start_long_press("SV", -0.1))
        self.ui.btnResIncrease.pressed.connect(lambda: self.start_long_press("Resistance", 5))
        self.ui.btnResDecrease.pressed.connect(lambda: self.start_long_press("Resistance", -5))

        # Stop increasing/decreasing when button is released
        self.ui.btnHRincrease.released.connect(self.stop_long_press)
        self.ui.btnHRdecrease.released.connect(self.stop_long_press)
        self.ui.btnSVincrease.released.connect(self.stop_long_press)
        self.ui.btnSVdecrease.released.connect(self.stop_long_press)
        self.ui.btnResIncrease.released.connect(self.stop_long_press)
        self.ui.btnResDecrease.released.connect(self.stop_long_press)

        self.update_labels()
    
    def toggle_start_reset(self):
        """Toggle between starting and resetting the motor."""
        if self.is_start_mode:
            print("TESTING: Start button pressed!")  # Debug
            start_motor()
            self.ui.resetButton.setText("RESET")
            self.ui.resetButton.setStyleSheet("background-color: yellow; color: black; font-size: 20px;")

            self.ui.stopButton.setEnabled(True)
            self.ui.stopButton.setStyleSheet("background-color: red; color: black; font-size: 20px;")

            self.ui.resetButton.setEnabled(False)  # Disable reset button until motor is stopped
        else:
            print("TESTING: Reset button pressed!")  # Debug
            self.reset_motor_function()
            self.ui.resetButton.setText("START")
            self.ui.resetButton.setStyleSheet("background-color: green; color: white; font-size: 20px;")

            self.ui.stopButton.setEnabled(False)
            self.ui.stopButton.setStyleSheet("background-color: lightgray; color: gray; font-size: 20px;")

        self.is_start_mode = not self.is_start_mode


    def stop_motor_function(self):
        """Stops the motor when the stop button is pressed."""
        print("TESTING: Stop button pressed!")  # Debug message
        self.disable_controls()
        stop_motor()  #

        self.ui.resetButton.setEnabled(True)  # Enable reset button again
    
    def reset_motor_function(self):
        """Resets the motor when the reset button is pressed."""
        print("TESTING: Reset button pressed!")  # Debug message
        self.enable_controls()
        reset_motor_position()

    def disable_controls(self):
        """Disables all interactive controls except the reset/start button."""
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.btnResistance.setEnabled(False)

        self.ui.btnHRincrease.setEnabled(False)
        self.ui.btnHRdecrease.setEnabled(False)
        self.ui.btnSVincrease.setEnabled(False)
        self.ui.btnSVdecrease.setEnabled(False)
        self.ui.btnResIncrease.setEnabled(False)
        self.ui.btnResDecrease.setEnabled(False)

        self.ui.stopButton.setEnabled(False)   # locking buttons (not all yet) except for the RESET/START button 

    def enable_controls(self):
        """Enables all interactive controls."""
        self.ui.pushButton.setEnabled(True)
        self.ui.pushButton_2.setEnabled(True)
        self.ui.btnResistance.setEnabled(True)
        self.ui.btnHRincrease.setEnabled(True)
        self.ui.btnHRdecrease.setEnabled(True)
        self.ui.btnSVincrease.setEnabled(True)
        self.ui.btnSVdecrease.setEnabled(True)
        self.ui.btnResIncrease.setEnabled(True)
        self.ui.btnResDecrease.setEnabled(True)

        self.ui.stopButton.setEnabled(True)


    def show_adjustment(self, stacked_widget, timer, page_index):
        """Switches to adjustment mode and starts a separate timer for each widget."""
        stacked_widget.setCurrentIndex(page_index)
        timer.start(3000)

    def start_long_press(self, parameter, step):
        """Start long-press adjustment with a delayed activation, then speed up over time."""
        self.hold_param = parameter
        self.hold_step = step
        self.hold_speed = 400

        # first step (single press)
        self.adjust_value(parameter, step)

        # Delay long-press activation for 800ms
        QtCore.QTimer.singleShot(800, self.activate_long_press)

    def activate_long_press(self):
        """Activates long-press with increasing speed."""
        if self.hold_param:
            self.hold_timer.start(self.hold_speed)

    def long_press_adjust(self):
        """Continuously adjust values while holding the button, speeding up over time."""
        if self.hold_param and self.hold_step:
            self.adjust_value(self.hold_param, self.hold_step)

            # Reduce interval time to speed up adjustments (minimum speed = 100ms)
            self.hold_speed = max(100, self.hold_speed - 50)
            self.hold_timer.setInterval(self.hold_speed)

    def stop_long_press(self):
        """Stop adjusting values when button is released."""
        self.hold_timer.stop()
        self.hold_param = None
        self.hold_step = 0
        self.hold_speed = 400

    def adjust_value(self, parameter, step):
        """Increase or decrease values when + or - buttons are pressed."""
        if parameter == "HR":
            self.heart_rate = max(10, min(120, self.heart_rate + step))
            self.hr_timer.start(3000)
        elif parameter == "SV":
            self.stroke_volume = max(0.5, min(2.5, round(self.stroke_volume + step, 1)))
            self.sv_timer.start(3000)
        elif parameter == "Resistance":
            self.resistance = max(0, min(100, self.resistance + step))
            self.res_timer.start(3000)

        self.update_labels()
        self.update_motor_parameters()  # Send data to Modbus

    def update_motor_parameters(self):
        """Runs motor update in a separate thread to prevent UI freezing."""
        print(f"TESTING: Starting ModbusThread with HR={self.heart_rate}, SV={self.stroke_volume}")  # Debug message
        self.modbus_thread = ModbusThread(self.heart_rate, self.stroke_volume)
        self.modbus_thread.start()

    def update_labels(self):
        """Update displayed values."""
        self.ui.pushButton.setText(f"HR = {self.heart_rate} BPM")
        self.ui.pushButton_2.setText(f"SV = {self.stroke_volume:.1f} cm")
        self.ui.btnResistance.setText(f"R = {self.resistance}%")

        self.ui.hrLabel.setText(f"{self.heart_rate} BPM")
        self.ui.svLabel.setText(f"{self.stroke_volume:.1f} cm")
        self.ui.resLabel.setText(f"{self.resistance}%")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
