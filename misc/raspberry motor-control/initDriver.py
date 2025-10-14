from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import time

# Configure Modbus RTU connection
client = ModbusClient(
    method='rtu',
    port='/dev/com2',
    baudrate=115200,
    parity='N',
    stopbits=1,
    bytesize=8,
    timeout=1
)

# Connect to the RS485 device
if not client.connect():
    print("Failed to connect to the Modbus device.")
    exit()

def write_register(address, value):
    """Write a single value to a Modbus register."""
    try:
        result = client.write_register(address, value, unit=1)  # Unit ID = 1 (Change if needed)
        if result.isError():
            print(f"Failed to write to register {hex(address)}")
        else:
            print(f"Successfully wrote {hex(value)} to register {hex(address)}")
    except Exception as e:
        print(f"Error: {e}")

def read_register(address):
    """Read a single value from a Modbus register."""
    try:
        result = client.read_holding_registers(address, 1, unit=1)  # Unit ID = 1
        if result.isError():
            print(f"Failed to read register {hex(address)}")
        else:
            value = result.registers[0]
            print(f"Value at register {hex(address)}: {hex(value)}")
            return value
    except Exception as e:
        print(f"Error: {e}")
        return None

try:
    # Enable servo: Write 0 to register 0x2009
    print("Enabling the servo motor...")
    write_register(0x2009, 0x0000)  # Servo enable
    write_register(0x6002, 0x0021)  # Set current position as homing position
    write_register(0x6006,0x0000)	#Set positive limit at 60000 (end position) HIGH BYTE 0000EA60 FFFF15A0
    write_register(0x6007,0xEA60)	#Set positive limit at 60000 (end position) LOW BYTE
    write_register(0x6008,0x0000)	#Set negative limit at 60000 (end position) HIGH BYTE
    write_register(0x6009,0x0001)	#Set negative limit at 60000 (end position) LOW BYTE
    
    # Path0 1.5 cm & 120 Hz
    write_register(0x6200, 0x4111)  # Path0 Mode (position mode, interrupt, abs position, jump to path1)
    write_register(0x6201, 0x0000)  # Target position high part
    write_register(0x6202, 0x7530)  # Target position low part (30000 steps overall)
    write_register(0x6203, 0x02D0)  # Set speed  = 720 rpm 
    write_register(0x6204, 0x0032)  # Set acceleration
    write_register(0x6205, 0x0032)  # Set deceleration
    write_register(0x6206, 0x0000)  # Pause time
    
    # PATH 1
    write_register(0x6208, 0x4011)  # Path1 Mode (jump to Path 0 back)
    write_register(0x6209, 0x0000)  # Target position high part (Zero/home)
    write_register(0x620A, 0x0000)  # Target position low part
    write_register(0x620B, 0x02D0)  # Set speed  = 720 rpm
    write_register(0x620C, 0x0032)  # Set acceleration
    write_register(0x620D, 0x0032)  # Set deceleration
    time.sleep(1)
    
    # Trigger PATH 0 (then automatically PATH 1)
    #write_register(0x6002, 0x0010)

    # Disable servo: Write 1 to register 0x2009 (if needed)
    # print("Disabling the servo motor...")
    # write_register(0x2009, 0x0001)

finally:
    # Close the Modbus connection
    client.close()
    print("Connection closed.")
