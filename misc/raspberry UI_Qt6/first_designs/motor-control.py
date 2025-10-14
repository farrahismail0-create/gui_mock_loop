import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import time


# Configure Modbus RTU connection
client = ModbusClient(
    method='rtu',
    port='/dev/com2',  # Replace with your RS485 port name
    baudrate=115200,
    parity='N',
    stopbits=1,
    bytesize=8,
    timeout=1
)

if not client.connect():
    print("Failed to connect to the Modbus device.")
    sys.exit()


def write_register(address, value):
    """Write a single value to a Modbus register."""
    try:
        result = client.write_register(address, value, unit=1)
        if result.isError():
            print(f"Failed to write to register {hex(address)}")
        else:
            print(f"Successfully wrote {hex(value)} to register {hex(address)}")
    except Exception as e:
        print(f"Error: {e}")


def calculate_speeds(hub: float, frequency: int):
    """Calculate systole speed, diastole speed, and pulses."""
    if not (0.5 <= hub <= 3):
        raise ValueError("Stroke must be between 0.5 and 3 cm.")
    if not (10 <= frequency <= 125):
        raise ValueError("Frequency must be between 10 and 125 BPM.")

    SteigungSpindel = 0.5  # Spindle pitch in cm/rev
    pulsesPerRotation = 10000  # Pulses per revolution

    pulse = int(hub / SteigungSpindel * pulsesPerRotation)
    cycle_time = 60 / frequency
    sys_time = cycle_time / 3
    dia_time = 2 * cycle_time / 3
    rounds = pulse / pulsesPerRotation

    forward_speed = int((rounds / sys_time) * 60)
    backward_speed = int((rounds / dia_time) * 60)

    return forward_speed, backward_speed, pulse


class MotorControlApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Motor Control Input")
        self.setGeometry(200, 200, 400, 200)

        layout = QVBoxLayout()

        self.freq_label = QLabel("Enter Frequency (10 - 125 BPM):")
        layout.addWidget(self.freq_label)
        self.freq_input = QLineEdit()
        layout.addWidget(self.freq_input)

        self.stroke_label = QLabel("Enter Stroke (0.5 - 3 cm):")
        layout.addWidget(self.stroke_label)
        self.stroke_input = QLineEdit()
        layout.addWidget(self.stroke_input)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.process_inputs)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def process_inputs(self):
        try:
            freq = float(self.freq_input.text())
            stroke = float(self.stroke_input.text())

            # Validate inputs
            if not 10 <= freq <= 125:
                raise ValueError("Frequency must be between 10 and 125 BPM.")
            if not 0.5 <= stroke <= 3:
                raise ValueError("Stroke must be between 0.5 and 3 cm.")

            # Calculate speeds and pulses
            sys_speed, dia_speed, target_position = calculate_speeds(stroke, freq)

            print(f"Systole Speed = {sys_speed}, Diastole Speed {dia_speed}, Pulses = {target_position}")
    
            # Path3 
            write_register(0x6218, 0x4411)  # Path3 Mode (position mode, interrupt, abs position, jump to path1)
            write_register(0x6219, 0x0000)  # Target position high part
            write_register(0x621A, target_position)  # Target position low part (30000 steps overall)
            write_register(0x621B, sys_speed)  # Set speed rpm 
            write_register(0x621C, 0x0032)  # Set acceleration
            write_register(0x621D, 0x0032)  # Set deceleration
            write_register(0x621E, 0x0000)  # Pause time
            
            # PATH 4
            write_register(0x6220, 0x4311)  # Path4 Mode (jump to Path 3 back)
            write_register(0x6221, 0x0000)  # Target position high part (Zero/Home)
            write_register(0x6222, 0x0000)  # Target position low part
            write_register(0x6223, dia_speed)  # Set speed rpm
            write_register(0x6224, 0x0032)  # Set acceleration
            write_register(0x6225, 0x0032)  # Set deceleration
            write_register(0x6226, 0x0000)  # Pause time
            time.sleep(1)
            
            # Trigger PATH 3 (then automatically PATH 1)
            write_register(0x6002, 0x0013)

            QMessageBox.information(self, "Success", f"Motor command sent!\n"
                                                     f"Frequency: {freq} BPM\n"
                                                     f"Stroke: {stroke} cm")

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send command: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotorControlApp()
    window.show()
    sys.exit(app.exec_())

# Close Modbus connection when the program ends
client.close()
