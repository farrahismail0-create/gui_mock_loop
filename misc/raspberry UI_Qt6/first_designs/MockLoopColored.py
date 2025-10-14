import sys
import logging
import os
import subprocess                                       #important to run other python code (motor control!) as a subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QFrame
from PyQt6.QtCore import QPropertyAnimation, QRect, QTimer
from main_window_colored import Ui_Dialog

os.environ["QT_STYLE_OVERRIDE"] = "Fusion"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Set initial values
        self.frequency = 10  # BPM (min: 10, max: 120)
        self.stroke_length = 0.5  # cm (min: 0.5, max: 3)

        # Update labels with initial values
        self.update_frequency_label()
        self.update_stroke_label()

        # Replace QPlainTextEdit with QTextEdit for color formatting
        self.ui.logTextEdit.setReadOnly(True)

        # Connect buttons to functions
        self.ui.increaseButton.clicked.connect(self.increase_frequency)
        self.ui.decreaseButton.clicked.connect(self.decrease_frequency)
        self.ui.increaseButton_2.clicked.connect(self.increase_stroke)
        self.ui.decreaseButton_2.clicked.connect(self.decrease_stroke)

        #stop and submit button
        self.ui.stopButton.clicked.connect(self.stop_motor)
        self.ui.submitButton.clicked.connect(self.submit_parameters)

        # hide the progress bar for now ! 
        self.ui.submitProgressBar.setVisible(False)
        #self.ui.submitProgressBar.hide() # this does the same as the line above


        # Initialize logging
        self.setup_logging()

        # Initialize state indicator
        self.update_state_indicator("")

        # Panel visibility states
        self.is_predefined_panel_visible = False
        self.is_history_panel_visible = False

        self.panel_x_hidden = self.width()  # Start position (off-screen)
        self.panel_x_visible = self.width() - 320  # Target position (on-screen)

        # Initialize panel positions
        self.ui.SlidingPanel.setGeometry(QRect(self.panel_x_hidden, 20, 311, 360))
        self.ui.historyPanel.setGeometry(QRect(self.panel_x_hidden, 20, 311, 360))

        # Connect buttons to their respective functions
        self.ui.predefinedButton.clicked.connect(self.toggle_predefined_panel)
        self.ui.historyButton.clicked.connect(self.toggle_history_panel)

        # Apply dark mode stylesheet
        dark_theme = """
            QWidget {
                background-color: #121212;
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2E3B4E;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #455A75;
            }
            QLabel {
                color: #ffffff;
            }
            QTextEdit {
                background-color: #222222;
                color: #ffffff;
                border: 1px solid #555555;
            }
                /* Green Submit Button */
                QPushButton#submitButton {
                    background-color: #28a745;
                    color: white;
                    font-weight: bold;
                }
                QPushButton#submitButton:hover {
                    background-color: #218838;
                }
                /* Red Stop Button */
                QPushButton#stopButton {
                    background-color: #dc3545;
                    color: white;
                    font-weight: bold;
                }
                QPushButton#stopButton:hover {
                    background-color: #c82333;
                }
        """
        self.setStyleSheet(dark_theme)

    #TODO initializing function for checking whether the motor is ready to 
    # start simulating ... (check if the motor in home position, check other parameters .....) 
    # while that the buttons should be unclickable ... 
    

    def update_frequency_label(self):
        self.ui.frequencyLabel.setText(f"Frequency = {self.frequency} BPM")

    def update_stroke_label(self):
        self.ui.StrokeLabel.setText(f"Stroke Length = {self.stroke_length:.1f} cm")

    def increase_frequency(self):
        if self.frequency < 120:
            self.frequency += 10
            self.update_frequency_label()
            self.log_message(f"Frequency increased to {self.frequency} BPM", "info")
        else:
            self.log_message("Maximum frequency reached!", "warning")

    def decrease_frequency(self):
        if self.frequency > 10:
            self.frequency -= 10
            self.update_frequency_label()
            self.log_message(f"Frequency decreased to {self.frequency} BPM", "info")
        else:
            self.log_message("Minimum frequency reached!", "warning")

    def increase_stroke(self):
        if self.stroke_length < 3.0:
            self.stroke_length += 0.1
            self.update_stroke_label()
            self.log_message(f"Stroke length increased to {self.stroke_length:.1f} cm", "info")
        else:
            self.log_message("Maximum stroke length reached!", "warning")

    def decrease_stroke(self):
        if self.stroke_length > 0.5:
            self.stroke_length -= 0.1
            self.update_stroke_label()
            self.log_message(f"Stroke length decreased to {self.stroke_length:.1f} cm", "info")
        else:
            self.log_message("Minimum stroke length reached!", "warning")

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
        self.logger.info("Application Started")

    def log_message(self, message, level="info"):
        """Logs a message to logTextEdit with color and updates stateLabel."""

        # Map levels to colors
        color_map = {
            "info": "green",
            "warning": "orange",
            "error": "red"
        }

        # Get the appropriate color
        color = color_map.get(level, "black")

        # Append message with HTML styling for color
        self.ui.logTextEdit.appendHtml(f'<span style="color: {color};">{message}</span>')

        # Update the state indicator color
        self.update_state_indicator(level)

        # Log message to console
        if level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)

    def update_state_indicator(self, level):
        """Updates the color of the state indicator based on the log level."""
        color_map = {
            "info": "green",
            "warning": "orange",
            "error": "red"
        }
        color = color_map.get(level, "gray")
        self.ui.stateLabel.setStyleSheet(f"background-color: {color}; border-radius: 20px;")

    def toggle_predefined_panel(self):
        """Toggle the SlidingPanel visibility and hide HistoryPanel if open."""
        if self.is_predefined_panel_visible:
            target_x = self.panel_x_hidden  # SlidingPanel off-screen
        else:
            target_x = self.panel_x_visible  # SlidingPanel on-screen

        # Animate SlidingPanel
        self.animation = QPropertyAnimation(self.ui.SlidingPanel, b"geometry")
        self.animation.setDuration(500)  # 500ms animation
        self.animation.setStartValue(self.ui.SlidingPanel.geometry())
        self.animation.setEndValue(QRect(target_x, 20, 311, 360))
        self.animation.start()

        # Hide HistoryPanel if open
        if self.is_history_panel_visible:
            self.ui.historyPanel.setGeometry(QRect(self.panel_x_hidden, 20, 311, 360))
            self.is_history_panel_visible = False

        # Toggle SlidingPanel state
        self.is_predefined_panel_visible = not self.is_predefined_panel_visible

    def toggle_history_panel(self):
        """Toggle the HistoryPanel visibility and hide SlidingPanel if open."""
        if self.is_history_panel_visible:
            target_x = self.panel_x_hidden  # HistoryPanel off-screen
        else:
            target_x = self.panel_x_visible  # HistoryPanel on-screen

        # Animate HistoryPanel
        self.animation = QPropertyAnimation(self.ui.historyPanel, b"geometry")
        self.animation.setDuration(500)  # 500ms 
        self.animation.setStartValue(self.ui.historyPanel.geometry())
        self.animation.setEndValue(QRect(target_x, 20, 311, 360))
        self.animation.start()

        # Hide SlidingPanel if open
        if self.is_predefined_panel_visible:
            self.ui.SlidingPanel.setGeometry(QRect(self.panel_x_hidden, 20, 311, 360))
            self.is_predefined_panel_visible = False

        # Toggle HistoryPanel state
        self.is_history_panel_visible = not self.is_history_panel_visible

    def stop_motor(self):
        """Handles the stop button functionality and runs back2zero.py in the background while capturing logs."""

        # Change state label to red
        self.update_state_indicator("error")

        # Disable the submit button and change its color to grey
        self.ui.submitButton.setDisabled(True)
        self.ui.submitButton.setStyleSheet("background-color: grey; color: white; font-weight: bold;")

        # Define the sequence of messages with delays
        messages = [
            "Brake / stopping the motor movement...",
            "Returning to home...",
            "Back in home position."
        ]

        # Function to log messages with delay
        def log_step(index):
            if index < len(messages):
                self.log_message(messages[index], "error")  # Log in red
                QTimer.singleShot(2000, lambda: log_step(index + 1))  # Delay 2 sec
            else:
                # Process finished
                self.update_state_indicator("info")  # Set state indicator back to green
                self.ui.submitButton.setDisabled(False)  # Re-enable submit button
                self.ui.submitButton.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")  # Green again

        try:
            # Adjust path for Raspberry Pi or local system
            script_path = os.path.join("C:/Users/Maher/OneDrive/Desktop/PRT/PRT2024/motor-control", "back2zero.py")   

            # Run back2zero.py asynchronously and capture output
            process = subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Function to read output in real-time
            def read_output():
                output = process.stdout.readline()
                if output:
                    self.log_message(output.strip(), "error")  # Log in red
                    QTimer.singleShot(500, read_output)  # Check again in 500ms
                elif process.poll() is not None:  # Process finished
                    log_step(0)  # Start logging sequence after script ends

            read_output()  # Start reading logs

        except FileNotFoundError:
            self.log_message("Error: back2zero.py not found!", "error")
            log_step(0)  # Still run log sequence even if script fails
    
    def submit_parameters(self):
        """Reads frequency and stroke length from the GUI, prints them, and stores them for later use."""

        # Read the current frequency and stroke length
        self.selected_frequency = self.frequency  # Store frequency
        self.selected_stroke_length = self.stroke_length  # Store stroke length

        # Print the values (for debugging purposes)
        print(f"Submitted Parameters -> Frequency: {self.selected_frequency} BPM, Stroke Length: {self.selected_stroke_length:.1f} cm")

        # Log the values in the GUI log box
        self.log_message(f"Submitted: Frequency = {self.selected_frequency} BPM, Stroke Length = {self.selected_stroke_length:.1f} cm", "info")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
