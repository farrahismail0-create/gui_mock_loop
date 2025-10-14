import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QPropertyAnimation, QRect
from main_window import Ui_Dialog

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

        # Connect buttons to functions
        self.ui.increaseButton.clicked.connect(self.increase_frequency)
        self.ui.decreaseButton.clicked.connect(self.decrease_frequency)
        self.ui.increaseButton_2.clicked.connect(self.increase_stroke)
        self.ui.decreaseButton_2.clicked.connect(self.decrease_stroke)

        # Initialize logging
        self.setup_logging()
        
        # Initialize state indicator
        self.update_state_indicator("info")
        
        # Initialize sliding panel state
        self.is_panel_visible = False
        self.ui.predefinedConditionsButton.clicked.connect(self.toggle_sliding_panel)
        self.panel_x_hidden = 1024  # Start position hidden
        self.panel_x_visible = 750   # Target position when shown
        self.ui.SlidingPanel.setGeometry(QRect(self.panel_x_hidden, 10, 270, 360))
        

    def setup_logging(self):
        """ Sets up logging to display messages in logTextEdit """
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
        self.logger.info("Application Started")

    def log_message(self, message, level="info"):
        """ Logs messages to the GUI with different colors """
        color = "black"  # Default color
        if level == "info":
            self.logger.info(message)
            color = "green"
        elif level == "warning":
            self.logger.warning(message)
            color = "orange"
        elif level == "error":
            self.logger.error(message)
            color = "red"
        
        # Append the log message with color styling
        self.ui.logTextEdit.appendHtml(f'<span style="color: {color};">{message}</span>')
        
        # Update the state indicator color
        self.update_state_indicator(level)

    def update_state_indicator(self, level):
        """ Updates the state indicator color dynamically """
        color = "gray"  # Default state color
        if level == "info":
            color = "green"
        elif level == "warning":
            color = "orange"
        elif level == "error":
            color = "red"
        
        self.ui.stateLabel.setStyleSheet(f"background-color: {color}; border-radius: 20px;")

    def toggle_sliding_panel(self):
        """ Toggles the sliding panel in and out """
        if self.is_panel_visible:
            new_x = self.panel_x_hidden  # Hide panel
        else:
            new_x = self.panel_x_visible  # Show panel
        
        self.animation = QPropertyAnimation(self.ui.SlidingPanel, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.ui.SlidingPanel.geometry())
        self.animation.setEndValue(QRect(new_x, self.ui.SlidingPanel.y(), self.ui.SlidingPanel.width(), self.ui.SlidingPanel.height()))
        self.animation.start()
        
        self.is_panel_visible = not self.is_panel_visible

    # Update frequency label
    def update_frequency_label(self):
        self.ui.frequencyLabel.setText(f"Frequency = {self.frequency} BPM")

    # Update stroke label
    def update_stroke_label(self):
        self.ui.StrokeLabel.setText(f"Stroke Length = {self.stroke_length:.1f} cm")

    # Increase frequency (+10)
    def increase_frequency(self):
        if self.frequency < 120:  # Upper limit
            self.frequency += 10
            self.update_frequency_label()
            self.log_message(f"Frequency increased to {self.frequency} BPM", "info")
        else:
            self.log_message("Maximum frequency reached!", "warning")

    # Decrease frequency (-10)
    def decrease_frequency(self):
        if self.frequency > 10:  # Lower limit
            self.frequency -= 10
            self.update_frequency_label()
            self.log_message(f"Frequency decreased to {self.frequency} BPM", "info")
        else:
            self.log_message("Minimum frequency reached!", "warning")

    # Increase stroke length (+0.1 cm)
    def increase_stroke(self):
        if self.stroke_length < 3.0:  # Upper limit
            self.stroke_length += 0.1
            self.update_stroke_label()
            self.log_message(f"Stroke length increased to {self.stroke_length:.1f} cm", "info")
        else:
            self.log_message("Maximum stroke length reached!", "warning")

    # Decrease stroke length (-0.1 cm)
    def decrease_stroke(self):
        if self.stroke_length > 0.5:  # Lower limit
            self.stroke_length -= 0.1
            self.update_stroke_label()
            self.log_message(f"Stroke length decreased to {self.stroke_length:.1f} cm", "info")
        else:
            self.log_message("Minimum stroke length reached!", "warning")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
