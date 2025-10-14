import serial

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
buffer=""

try:
	while True:
		data = ser.read(ser.in_waiting or 1).decode("utf-8", errors="ignore")
		if data:
			buffer += data
			
			while True:
				start = buffer.find("#")
				end = buffer.find(";", start)
				
				if start != -1 and end != -1 and end > start:
					raw_packet = buffer[start + 1:end]
					buffer = buffer[end + 1]
					
					try:
						values = list(map(float, raw_packet.split(",")))
						print(f"Received values: {values}")
						
					except ValueError:
						print("Malformed packet", raw_packet)
				else:
					break
				
except KeyboardInterrupt:
	print("Exiting...")
	ser.close()
				
