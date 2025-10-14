import sys
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QPushButton, QHeaderView
from PyQt6.QtCore import QDateTime
from main_window_tabs import Ui_ImpellaMockLoopGUI  # UI class for main window
from history_file import save_history_to_json, load_history_from_json, delete_history_entry


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ImpellaMockLoopGUI()  
        self.ui.setupUi(self)  

        # Force the first tab (Parameter Setting) to be active on startup
        self.ui.tabWidget.setCurrentIndex(0)

        # Setup history table
        self.setup_history_table()

        # Load history from JSON (only once)
        self.load_history_into_table()

        # Connect Submit button to add settings to history
        self.ui.submitButton.clicked.connect(self.submit_configuration)

    def submit_configuration(self):
        """Handles the Submit button click event by adding new settings to history."""
        
        # TODO
        # Example: Retrieve values from UI elements
        frequency = 80 
        stroke = 1.5  

        # Add the new settings to history
        self.add_to_history(frequency, stroke)


    def add_to_history(self, frequency: int, stroke: float, timestamp=None):
        """Adds a new row to the history table if it does not already exist."""
        
        # Ensure timestamp is always assigned
        if timestamp is None:
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

        # Check if the entry already exists (to avoid duplicates)
        for row in range(self.ui.historyTableWidget.rowCount()):
            existing_timestamp = self.ui.historyTableWidget.item(row, 0)
            if existing_timestamp and existing_timestamp.text() == timestamp:
                return  # Entry already exists, do not add a duplicate

        # Add new row
        row = self.ui.historyTableWidget.rowCount()
        self.ui.historyTableWidget.insertRow(row)

        # Format settings string
        settings_str = f"Frequency: {frequency} BPM, Stroke: {stroke} cm"

        # Add Timestamp
        self.ui.historyTableWidget.setItem(row, 0, QTableWidgetItem(timestamp))

        # Add Settings
        self.ui.historyTableWidget.setItem(row, 1, QTableWidgetItem(settings_str))

        # Create a container widget for both buttons (Replay & Delete)
        button_widget = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Replay Button
        replay_button = QPushButton("Replay")
        replay_button.clicked.connect(lambda: self.replay_settings(frequency, stroke))

        # Delete Button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.delete_history_row(row, timestamp))

        # Add buttons to the layout
        button_layout.addWidget(replay_button)
        button_layout.addWidget(delete_button)

        # Set the widget containing both buttons in the third column
        self.ui.historyTableWidget.setCellWidget(row, 2, button_widget)

        # Save to JSON only if it is a new entry
        save_history_to_json(timestamp, frequency, stroke)

    def load_history_into_table(self):
        """Loads history from JSON file and populates the table without duplicates."""
        self.ui.historyTableWidget.setRowCount(0)  # Clear existing rows before loading

        history_data = load_history_from_json()
        for entry in history_data:
            self.add_to_history(entry["frequency"], entry["stroke"], entry["timestamp"])

    def setup_history_table(self):
        """Configures the history table to properly fit inside the tab."""
        self.ui.historyTableWidget.setColumnCount(3)
        self.ui.historyTableWidget.setHorizontalHeaderLabels(["Timestamp", "Settings", "Action"])

        # Stretch columns to fit the entire width of the table
        header = self.ui.historyTableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Timestamp column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Settings column
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Replay/Delete buttons

        # Remove row numbers
        self.ui.historyTableWidget.verticalHeader().setVisible(False)

    def replay_settings(self, frequency: int, stroke: float):
        """Reapply saved settings to the UI when 'Replay' is clicked."""
        print(f"Replaying settings - Frequency: {frequency} BPM, Stroke: {stroke} cm")

        # Apply the values back to the input fields
        self.ui.frequencyLabel.setText(f"Frequency = {frequency} BPM")
        self.ui.StrokeLabel.setText(f"Stroke Length = {stroke} cm")

    def delete_history_row(self, row: int, timestamp: str):
        """Deletes a row from the history table and removes it from the JSON file."""
        # Remove entry from JSON
        delete_history_entry(timestamp)

        # Remove row from table
        self.ui.historyTableWidget.removeRow(row)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
