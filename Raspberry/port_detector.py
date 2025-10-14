from serial.tools import list_ports

serial_number_arduino_nano = "TODO"         # usb-1a86_USB_Serial-if00-port0
serial_number_rs485_usb_converter = "TODO"  # 

# List all connected serial ports and their serial numbers 
print("Available serial devices:\n")
for port in list_ports.comports():
    print(f"Device: {port.device} | Serial: {port.location} | Desc: {port.description}")
#    print(f"{port.description}:{port.interface}:{port.product}\n")

print("\nSearching for known serial numbers...\n")

# --- Arduino Nano Detection ---
try:
    comport_arduino_nano = next(list_ports.grep(serial_number_arduino_nano)).device
    print(f" Arduino Nano found at {comport_arduino_nano} (Serial: {serial_number_arduino_nano})")
except StopIteration:
    print(f" Arduino Nano with serial '{serial_number_arduino_nano}' not found.")

# --- Sonoflow RS485 Detection --- 
try:
    comport_sonoflow = next(list_ports.grep(serial_number_rs485_usb_converter)).device
    print(f" Sonoflow Bus Converter found at {comport_sonoflow} (Serial: {serial_number_rs485_usb_converter})")
except StopIteration:
    print(f" Sonoflow Converter with serial '{serial_number_rs485_usb_converter}' not found.")
