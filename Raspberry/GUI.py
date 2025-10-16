# GUI_3.0.py – Final integrated GUI with live plotting, motor control, and UI

import sys
from PyQt5 import QtWidgets, QtCore
# from PyQt5 import QtGui
# import pyqtgraph as pg
# import random
# import math
# import numpy as np
from ui_elements import Ui_MainWindow
from modbus_controller import ModbusController
from live_plotter import LivePlotter
# from live_plotter_calibration_test import LivePlotter
from sensor_reader_thread import SensorReaderThread


# Reuse ModbusThread from previous design
class ModbusThread(QtCore.QThread):
    """Thread to update motor parameters without freezing the GUI."""

    def __init__(self, modbus, frequency, stroke_volume):
        super().__init__()
        self.modbus = modbus
        self.frequency = frequency
        self.stroke_volume = stroke_volume

    def run(self):
        """Send updated motor values to Modbus."""
        try:
            # print(f"TESTING: ModbusThread started with Frequency={self.frequency}, Stroke={self.stroke_volume}")  # Debug message
            # set_motor_speed(self.frequency, self.stroke_volume)  # OLD
            # set_motor_target_position(self.frequency, self.stroke_volume)  # OLD
            self.modbus.set_motor_speed(self.frequency, self.stroke_volume)  # NEW from ModbusController CLASS
            self.modbus.set_motor_target_position(self.frequency, self.stroke_volume)  # NEW from ModbusController CLASS
        except Exception as e:
            print(f"Modbus Error: {e}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.showFullScreen()

        self.ui.setupUi(self)
        self.ui.devButton.clicked.connect(self.enter_developer_mode)

        self.modbus = ModbusController()  # Instantiate the new ModbusController CLASS

        # Apply dark theme stylesheet
        self.setStyleSheet("""
             QWidget {
                 background-color: #000000;
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
                 background-color: #000000;
             }
             QMenu {
                 background-color: #3c3f41;
                 color: white;
                 border: 1px solid #5c5c5c;
             }
             QMenu::item {
                 padding: 5px 20px 5px 20px;
             }
             QMenu::item:selected {
                 background-color: #505357;
             }
         """)
        # Set initial values  (should be read from Modbus on startup)
        # These value should be read from starting when first starting the GUI
        self.heart_rate = 60
        self.stroke_volume = 1.5
        self.resistance = 50

        # Recording state variables
        self.is_recording = False
        self.record_start_time = None
        self.record_elapsed_time = 0

        # Embed live plotter
        """self.plotter = LivePlotter(self)
        self.plotter.setGeometry(40, 130, 700, 430)
        self.plotter.setParent(self)"""
        self.plotter = LivePlotter(self.ui.centralwidget)
        self.plotter.setGeometry(182, 130, 700, 430)
        self.plotter.stats_updated.connect(self.update_pressure_labels)
        self.plotter.show()

        self.plotter.stats_updated.connect(self.update_pressure_labels)

        # Create and setup settings menu
        self.setup_settings_menu()

        # Sensor Reader Thread
        self.sensor_thread = SensorReaderThread(port="/dev/ttyUSB0")
        self.sensor_thread.data_received.connect(self.handle_sensor_data)
        self.sensor_thread.calibration_finished.connect(self.on_calibration_finished)
        self.sensor_thread.start()

        # All UI initializations from GUI_2.0
        self.initialize_ui_logic()

    def initialize_ui_logic(self):
        self.hr_timer = QtCore.QTimer(singleShot=True)
        self.hr_timer.timeout.connect(lambda: self.ui.hrStackedWidget.setCurrentIndex(1))
        self.sv_timer = QtCore.QTimer(singleShot=True)
        self.sv_timer.timeout.connect(lambda: self.ui.svStackedWidget.setCurrentIndex(1))
        self.res_timer = QtCore.QTimer(singleShot=True)
        self.res_timer.timeout.connect(lambda: self.ui.resStackedWidget.setCurrentIndex(0))

        self.hold_timer = QtCore.QTimer()
        self.hold_timer.timeout.connect(self.long_press_adjust)

        # Recording timer
        self.record_timer = QtCore.QTimer()
        self.record_timer.timeout.connect(self.update_record_timer)

        self.hold_param = None
        self.hold_step = 0
        self.hold_speed = 400

        self.log_buffer = ""
        self._drag_pos = None

        # Track current state of the RESET/START button
        self.ui.resetButton.setText("START\nMOTOR")
        self.is_start_mode = True
        self.ui.stopButton.setStyleSheet("background-color: red; color: black; font-size: 20px;")
        self.ui.resetButton.setStyleSheet("background-color: green; color: white; font-size: 20px;")

        # STOP and RESET/START BUTTONs
        self.ui.stopButton.clicked.connect(self.stop_motor_function)
        self.ui.resetButton.clicked.connect(self.toggle_start_reset)

        # Connect record button
        self.ui.recordButton.clicked.connect(self.toggle_recording)


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

        # Connect buttons to toggle plots
        self.ui.lvpLabel.clicked.connect(lambda: self.plotter.toggle_channel("LVP"))
        self.ui.aopLabel.clicked.connect(lambda: self.plotter.toggle_channel("AOP"))
        self.ui.lapLabel.clicked.connect(lambda: self.plotter.toggle_channel("LAP"))
        self.ui.flowLabel.clicked.connect(lambda: self.plotter.toggle_channel("FLOW"))

        # Button styling map
        button_styles = {
            self.ui.lvpLabel: "color: green; background-color: black; font-weight: bold; border: none;",
            self.ui.aopLabel: "color: red; background-color: black; font-weight: bold; border: none;",
            self.ui.lapLabel: "color: yellow; background-color: black; font-weight: bold; border: none;",
            self.ui.flowLabel: "color: cyan; background-color: black; font-weight: bold; border: none;",
        }

        # Apply to each pressure label (now QPushButton)
        for button, style in button_styles.items():
            button.setStyleSheet(style)

        self.ui.calibrateButton.clicked.connect(self.calibrate_sensors)

        self.ui.stateIndicator.mousePressEvent = self.toggle_log_dialog
        self.setup_log_dialog()

        self.update_labels()

        self.update_record_button()

    def toggle_recording(self):

        """Toggle recording state and start/stop timer"""

        if not self.is_recording:

            # Start recording

            self.is_recording = True

            self.record_start_time = QtCore.QTime.currentTime()

            self.record_elapsed_time = QtCore.QTime(0, 0, 0, 0)

            self.record_timer.start(100)  # Update every 100ms for smooth display

            self.log_message("Recording started", "info")

        else:

            # Stop recording

            self.is_recording = False

            self.record_timer.stop()

            recording_duration = self.format_time_ms(self.record_elapsed_time)

            self.log_message(f"Recording stopped. Duration: {recording_duration}", "done")

            # Reset timer display on the button

            self.ui.recordButton.setText("RECORD")

        self.update_record_button()

    def update_record_timer(self):

        """Update the recording timer display"""

        if self.is_recording and self.record_start_time:
            current_time = QtCore.QTime.currentTime()
            self.record_elapsed_time = self.record_start_time.msecsTo(current_time)
            self.ui.recordButton.setText(f"REC\n{self.format_time_ms(self.record_elapsed_time)}")

    def format_time_ms(self, ms: int) -> str:
        minutes = (ms // 60000) % 60
        seconds = (ms // 1000) % 60
        centis = (ms % 1000) // 10  # two digits
        return f"{minutes:02d}:{seconds:02d}.{centis:02d}"

    def update_record_button(self):

        """Update record button appearance based on recording state"""

        if self.is_recording:

            self.ui.recordButton.setStyleSheet("""

                background-color: #ff4444; 

                color: white; 

                font-size: 16px;

                font-weight: bold;

            """)

        else:

            self.ui.recordButton.setStyleSheet("""

                background-color: #3c3f41;

                color: #ffffff;

                font-size: 16px;

            """)

    def setup_settings_menu(self):
        """Create the drop-down menu for settings button"""
        self.settings_menu = QtWidgets.QMenu(self)

        # Add menu actions
        self.developer_mode_action = QtWidgets.QAction("Developer Mode", self)
        self.appearance_action = QtWidgets.QAction("Appearance Settings", self)
        self.data_management_action = QtWidgets.QAction("Data Management", self)
        self.system_info_action = QtWidgets.QAction("System Information", self)
        self.about_action = QtWidgets.QAction("About", self)
        self.exit_action = QtWidgets.QAction("Exit to OS", self)

        # Connect actions to functions
        self.developer_mode_action.triggered.connect(self.enter_developer_mode)
        self.appearance_action.triggered.connect(self.show_appearance_settings)
        self.data_management_action.triggered.connect(self.show_data_management)
        self.system_info_action.triggered.connect(self.show_system_info)
        self.about_action.triggered.connect(self.show_about)
        self.exit_action.triggered.connect(self.exit_to_os)

        # Add actions to menu
        self.settings_menu.addAction(self.developer_mode_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(self.appearance_action)
        self.settings_menu.addAction(self.data_management_action)
        self.settings_menu.addAction(self.system_info_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(self.about_action)
        self.settings_menu.addAction(self.exit_action)

        # Set the menu to the settings button
        self.ui.settingsButton.setMenu(self.settings_menu)

    def enter_developer_mode(self):
        """Developer mode with password protection"""
        text, ok = QtWidgets.QInputDialog.getText(self, "Developer Mode", "Enter passcode:",
                                                  QtWidgets.QLineEdit.Password)
        if ok and text == "raspberry":
            QtWidgets.QMessageBox.information(self, "Developer Mode", "Developer mode activated!")
            # Add developer mode functionality here
        elif ok:
            QtWidgets.QMessageBox.warning(self, "Access Denied", "Incorrect passcode!")

    def show_appearance_settings(self):
        """Show appearance settings dialog"""
        QtWidgets.QMessageBox.information(self, "Appearance Settings", "Appearance settings dialog would open here.")

    def show_data_management(self):
        """Show data management dialog"""
        QtWidgets.QMessageBox.information(self, "Data Management", "Data management dialog would open here.")

    def show_system_info(self):
        """Show system information"""
        info = """
        System Information:

        - Heart Rate: {} BPM
        - Stroke Volume: {} cm
        - Resistance: {}%
        - Motor Status: {}
        - Recording: {}
        Software Version: 3.0
        """.format(self.heart_rate, self.stroke_volume, self.resistance,
                   "Running" if not self.is_start_mode else "Stopped",
                   "Active" if self.is_recording else "Inactive")

        QtWidgets.QMessageBox.information(self, "System Information", info)

    def show_about(self):
        """Show about dialog"""
        about_text = """
        Cardiac Simulator GUI v3.0

        Advanced cardiac simulation interface
        with real-time plotting and motor control.

        Developed for medical training and research.
        """
        QtWidgets.QMessageBox.about(self, "About", about_text)

    def exit_to_os(self):
        """Exit the application and return to OS"""
        # Stop recording if active
        if self.is_recording:
            self.toggle_recording()

        reply = QtWidgets.QMessageBox.question(self, "Exit Confirmation",
                                               "Are you sure you want to exit to OS?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.close()

    def handle_sensor_data(self, sensor_id, value):
        if sensor_id == 0:
            self.plotter.receive_data("LVP", value)
        elif sensor_id == 1:
            self.plotter.receive_data("AOP", value)
        elif sensor_id == 2:
            self.plotter.receive_data("LAP", value)

    def calibrate_sensors(self):
        if self.is_start_mode:  # Motor is not running
            self.sensor_thread.request_calibration.emit()
            # self.log_message("Sensor zeroing started...", "info")
            print("Sensor zeroing started...")
        else:
            # self.log_message("Cannot calibrate while motor is running.", "warning")
            print("Cannot calibrate while motor is running.")

    def on_calibration_finished(self, offsets):
        # print(f"Sensor calibration complete. New zero offsets: {offsets}")
        pass  # Do nothing for now

    def toggle_start_reset(self):
        """Toggle between starting and resetting the motor."""
        if self.is_start_mode:
            # print("TESTING: Start button pressed!")  # Debug
            # start_motor()  # OLD
            self.modbus.start_motor()  # NEW from ModbusController CLASS
            self.ui.resetButton.setText("RESET\nMOTOR")

            self.ui.stopButton.setEnabled(True)
            # self.ui.stopButton.setStyleSheet("background-color: red; color: black; font-size: 20px;")

            self.ui.resetButton.setEnabled(False)
            # self.ui.resetButton.setStyleSheet("background-color: lightgray; color: gray; font-size: 20px;")

        else:
            # print("TESTING: Reset button pressed!")  # Debug
            self.reset_motor_function()
            self.ui.resetButton.setText("START\nMOTOR")
            self.ui.resetButton.setStyleSheet("background-color: green; color: white; font-size: 20px;")

            self.ui.stopButton.setEnabled(False)
            self.ui.stopButton.setStyleSheet("background-color: lightgray; color: gray; font-size: 20px;")

        self.is_start_mode = not self.is_start_mode

    def stop_motor_function(self):
        """Stops the motor when the stop button is pressed."""
        # print("TESTING: Stop button pressed!")  # Debug message
        self.disable_controls()
        # stop_motor()  # OLD
        self.modbus.stop_motor()  # NEW from ModbusController CLASS
        self.ui.resetButton.setEnabled(True)
        self.ui.resetButton.setStyleSheet("background-color: yellow; color: black; font-size: 20px;")

    def reset_motor_function(self):
        """Resets the motor when the reset button is pressed."""
        # print("TESTING: Reset button pressed!")  # Debug message
        self.enable_controls()
        # reset_motor_position()  # OLD
        self.modbus.reset_motor_position()  # NEW from ModbusController CLASS

    def disable_controls(self):  # STILL NOT PROBERLY WORKING
        for widget in [
            self.ui.pushButton, self.ui.pushButton_2, self.ui.btnResistance,
            self.ui.btnHRincrease, self.ui.btnHRdecrease,
            self.ui.btnSVincrease, self.ui.btnSVdecrease,
            self.ui.btnResIncrease, self.ui.btnResDecrease,
            self.ui.stopButton, self.ui.calibrateButton
        ]:
            widget.setEnabled(False)

    def enable_controls(self):  # STILL NOT PROBERLY WORKING
        for widget in [
            self.ui.pushButton, self.ui.pushButton_2, self.ui.btnResistance,
            self.ui.btnHRincrease, self.ui.btnHRdecrease,
            self.ui.btnSVincrease, self.ui.btnSVdecrease,
            self.ui.btnResIncrease, self.ui.btnResDecrease,
            self.ui.stopButton, self.ui.calibrateButton
        ]:
            widget.setEnabled(True)

    # ------------------------------------- Labels --------------------------------
    def show_adjustment(self, stacked_widget, timer, page_index):
        """Switches to adjustment mode and starts a separate timer for each widget."""
        stacked_widget.setCurrentIndex(page_index)
        timer.start(3000)

    def start_long_press(self, parameter, step):
        """Start long-press adjustment with a delayed activation, then speed up over time."""
        self.hold_param = parameter
        self.hold_step = step
        self.hold_speed = 400
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
        # print(f"TESTING: Starting ModbusThread with HR={self.heart_rate}, SV={self.stroke_volume}")  # Debug Message
        self.modbus_thread = ModbusThread(self.modbus, self.heart_rate, self.stroke_volume)
        self.modbus_thread.start()

    def update_labels(self):
        """Update displayed values."""
        self.ui.pushButton.setText(f"HR = {self.heart_rate} BPM")
        self.ui.pushButton_2.setText(f"SV = {self.stroke_volume:.1f} cm")
        self.ui.btnResistance.setText(f"R = {self.resistance}%")

        self.ui.hrLabel.setText(f"{self.heart_rate} BPM")
        self.ui.svLabel.setText(f"{self.stroke_volume:.1f} cm")
        self.ui.resLabel.setText(f"{self.resistance}%")

    def update_pressure_labels(self, name, stats):
        """Update the corresponding QLabel for pressure/flow."""
        if name == "LVP":
            self.ui.lvpLabel.setText(f"LVP\n{int(stats['systole'])}/{int(stats['diastole'])}")
        elif name == "AOP":
            self.ui.aopLabel.setText(f"AOP\n{int(stats['systole'])}/{int(stats['diastole'])}")
        elif name == "LAP":
            self.ui.lapLabel.setText(f"LAP\n{int(stats['systole'])}/{int(stats['diastole'])}")
        elif name == "FLOW":
            self.ui.flowLabel.setText(f"FLOW\n{stats['mean']:.1f}")

    # ---------------------------------------- Log Window ---------------------------------

    def update_state_indicator(self, state):  # NOT USED
        color_map = {
            "idle": "gray",
            "running": "green",
            "error": "red"
        }
        color = color_map.get(state, "gray")
        self.ui.stateIndicator.setStyleSheet(f"""
            background-color: {color};
            border-radius: 20px;
            border: 2px solid black;
        """)

    def setup_log_dialog(self):
        self.log_dialog = QtWidgets.QDialog(self)
        self.log_dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog)
        self.log_dialog.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.log_dialog.setModal(False)
        self.log_dialog.setFixedSize(420, 320)

        log_container = QtWidgets.QWidget(self.log_dialog)
        log_container.setGeometry(0, 0, 420, 320)
        log_container.setStyleSheet("background-color: rgba(40, 40, 60, 230); border-radius: 10px;")

        self.log_close_btn = QtWidgets.QPushButton("X", log_container)
        self.log_close_btn.setGeometry(390, 5, 24, 24)
        self.log_close_btn.setStyleSheet("background-color: red; color: white; font-weight: bold; border-radius: 12px;")
        self.log_close_btn.clicked.connect(self.log_dialog.hide)

        self.log_text = QtWidgets.QTextEdit(log_container)
        self.log_text.setGeometry(10, 35, 400, 275)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: transparent; color: #00ffff; font-size: 14px; border: none;")

    def toggle_log_dialog(self, event):
        if self.log_dialog.isVisible():
            self.log_dialog.hide()
        else:
            pos = self.mapToGlobal(QtCore.QPoint(self.width() - 450, 70))
            self.log_dialog.move(pos)
            self.log_dialog.show()

    def log_message(self, message, level="info"):
        color_map = {
            "done": "lightgreen",
            "warning": "yellow",
            "error": "red",
            "info": "white"
        }
        color = color_map.get(level, "white")
        formatted = f'<span style="color:{color}">{message}</span><br>'
        self.log_buffer += formatted
        self.log_text.setHtml(self.log_buffer)

    def dialog_mouse_press(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.log_dialog.frameGeometry().topLeft()
            event.accept()

    def dialog_mouse_move(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self._drag_pos:
            self.log_dialog.move(event.globalPos() - self._drag_pos)
            event.accept()

    def closeEvent(self, event):
        # Stop recording if active
        if self.is_recording:
            self.toggle_recording()
        self.sensor_thread.stop()
        event.accept()


# --------------------------------- MAIN ---------------------------------------


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())