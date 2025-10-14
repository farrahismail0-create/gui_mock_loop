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
    print("getting the motor home !!!")
    write_register(0x2009, 0x0000) # servo enable
    write_register(0x6002, 0x0040) # e-stop
    
    # PATH 15 (Last PATH)
    write_register(0x6278, 0x0011)  # Path15 Mode (dont jump)
    write_register(0x6279, 0x0000)  # Target position high part (Zero/home)
    write_register(0x627A, 0x0000)  # Target position low part
    write_register(0x627B, 0x0032)  # Set speed
    write_register(0x627C, 0x0032)  # Set acceleration
    write_register(0x627D, 0x0032)  # Set deceleration
    time.sleep(1)
    
    #write_register(0x6002, 0x0021) # set current position as homing position
    #write_register(0x600A, 0x0107) # 1-with Z signal, 5-positive direction and homing switch detect (6 for negative direction)
    #write_register(0x600B, 0x0000) # Homing position H 
    #write_register(0x600C, 0x1388) # Homing position L auf -5000 = -0.25 cm  (0x2710 -> 10000 = 0.5 cm)
    #write_register(0x600F, 0x0064) # homing high speed 100 rpm
    #write_register(0x6010, 0x0019) # homing low speed 25 rpm
    #write_register(0x6011, 0x0032) # homing acceleration 50
    #write_register(0x6012, 0x0032) # homing deceleration 50
    
    write_register(0x6002, 0x0021) # set current position as homing position
    write_register(0x600A, 0x0105) # 1-with Z signal, 5-positive direction and homing switch detect (6 for negative direction)
    write_register(0x600B, 0xFFFF) # Homing position H 
    write_register(0x600C, 0xEEA4 ) # Homing position L auf -5000 = -0.25 cm  (0x2710 -> 10000 = 0.5 cm)
    write_register(0x600F, 0x0064) # homing high speed 100 rpm
    write_register(0x6010, 0x0019) # homing low speed 25 rpm
    write_register(0x6011, 0x0032) # homing acceleration 50
    write_register(0x6012, 0x0032) # homing deceleration 50
    
    write_register(0x6002, 0x0020) # homing start
    
    
    # Trigger PATH 15
    #write_register(0x6002, 0x001F)
    
    
    
    

finally:
    # Close the Modbus connection
    client.close()
    print("Connection closed.")




