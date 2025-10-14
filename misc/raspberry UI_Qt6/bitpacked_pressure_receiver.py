import serial

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Store partial readings per sensor
partial_data = {
    0: {'low': None, 'high': None},
    1: {'low': None, 'high': None},
    2: {'low': None, 'high': None}
}

print("Listening for binary sensor data...\n")

try:
    while True:
        if ser.in_waiting:
            raw_byte = ser.read(1)
            byte = raw_byte[0]  # convert to int

            flag      = byte & 0b00000001
            sensor_id = (byte >> 1) & 0b00000011
            pressure_bits = (byte >> 3) & 0b00011111

            if flag == 0:
                # Low byte (P4–P0)
                partial_data[sensor_id]['low'] = pressure_bits
            else:
                # High byte (P9–P5)
                partial_data[sensor_id]['high'] = pressure_bits

            # When we have both parts, reconstruct
            if partial_data[sensor_id]['low'] is not None and partial_data[sensor_id]['high'] is not None:
                low  = partial_data[sensor_id]['low']
                high = partial_data[sensor_id]['high']
                full_pressure = (high << 5) | low

                print(f"Sensor {sensor_id + 1}: Pressure = {full_pressure}")

                # Reset after reading
                partial_data[sensor_id]['low'] = None
                partial_data[sensor_id]['high'] = None

except KeyboardInterrupt:
    print("\nExiting...")
    ser.close()
