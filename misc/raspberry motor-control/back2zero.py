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
        result = client.write_register(address, value, unit=1)
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
    print("Stopping the servo motor...")
    write_register(0x2009, 0x0000)  # Servo enable
    write_register(0x6002, 0x0040)  # E-Stop!!
    
    # PATH 15 (Last PATH)
    write_register(0x6278, 0x0011)  # Path15 Mode (dont jump)
    write_register(0x6279, 0x0000)  # Target position high part (Zero/home)
    write_register(0x627A, 0x0000)  # Target position low part
    write_register(0x627B, 0x0032)  # Set speed
    write_register(0x627C, 0x0032)  # Set acceleration
    write_register(0x627D, 0x0032)  # Set deceleration
    time.sleep(1)
    
    # Trigger PATH 15
    write_register(0x6002, 0x001F)

    # Disable servo: Write 1 to register 0x2009 (if needed)
    # print("Disabling the servo motor...")
    #write_register(0x2009, 0x0001)

finally:
    # Close the Modbus connection
    client.close()
    print("Connection closed.")



