import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)


class SimpleInterface(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle("Motor Control Input")
        self.setGeometry(200, 200, 300, 200)

        # Create a layout
        layout = QVBoxLayout()

        # Frequency Input
        self.freq_label = QLabel("Enter Frequency (30 - 120 BPM):")
        layout.addWidget(self.freq_label)
        self.freq_input = QLineEdit()
        layout.addWidget(self.freq_input)

        # Stroke Input
        self.stroke_label = QLabel("Enter Stroke (0.5 - 3 cm):")
        layout.addWidget(self.stroke_label)
        self.stroke_input = QLineEdit()
        layout.addWidget(self.stroke_input)

        # Submit Button
        self.submit_button = QPushButton()
        self.submit_button.setText("Submit")
        self.submit_button.clicked.connect(self.process_inputs)
        layout.addWidget(self.submit_button)

        # Set layout to the window
        self.setLayout(layout)

    def process_inputs(self):
        try:
            # Get and validate frequency
            freq = float(self.freq_input.text())
            if not 30 <= freq <= 120:
                raise ValueError("Frequency must be between 30 and 120 BPM.")

            # Get and validate stroke
            stroke = float(self.stroke_input.text())
            if not 0.5 <= stroke <= 3:
                raise ValueError("Stroke must be between 0.5 and 3 cm.")

            # If valid, display success message
            QMessageBox.information(self, "Success", f"Frequency: {freq} BPM\nStroke: {stroke} cm")

        except ValueError as e:
            # Display error message
            QMessageBox.warning(self, "Invalid Input", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleInterface()
    window.show()
    sys.exit(app.exec_())