import serial

# Serial port configuration
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Store partial readings per sensor
partial_data = {
    0: {'low': None, 'high': None},
    1: {'low': None, 'high': None},
    2: {'low': None, 'high': None}
}

print("Listening for binary sensor data on", SERIAL_PORT, "...\n")

# Conversion constants
VREF = 3.27  # External reference voltage in Volts
sensor1_OFFSET = 118
sensor2_OFFSET = 135
sensor3_OFFSET = 123
#SENSITIVITY = 0.0072  # Sensor sensitivity (V/mmHg)
#measured_mmHg = 150   # More acurate measurment are needed !!!
#measured_Voltage = 1.63  # More acurate measurment are needed !!!

# Calibration data
sensor1_k = (330 - 0) / (932 - 118)
sensor2_k = (330 - 0) / (920 - 135)
sensor3_k = (330 - 0) / (914 - 123)

try:
    while True:
        if ser.in_waiting:
            raw_byte = ser.read(1)
            byte = raw_byte[0]  # Convert byte to integer

            flag = byte & 0b00000001
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
                low = partial_data[sensor_id]['low']
                high = partial_data[sensor_id]['high']
                pressure_adc = (high << 5) | low
                
                #voltage = (pressure_adc / 1023.0) * VREF

                if sensor_id == 0:
                    pressure_mmHg = sensor1_k * (pressure_adc - sensor1_OFFSET)
                elif sensor_id == 1:
                    pressure_mmHg = sensor2_k * (pressure_adc - sensor2_OFFSET)
                elif sensor_id == 2:
                    pressure_mmHg = sensor3_k * (pressure_adc - sensor3_OFFSET)
                #else:
                    #pressure_mmHg = 0  # fallback

                print(f"Sensor {sensor_id + 1}: {pressure_mmHg:.2f} mmHg (raw={pressure_adc})")
                #, voltage={voltage:.3f} V)")

                # Reset after reading
                partial_data[sensor_id]['low'] = None
                partial_data[sensor_id]['high'] = None

except KeyboardInterrupt:
    print("\nExiting...")
    ser.close()
