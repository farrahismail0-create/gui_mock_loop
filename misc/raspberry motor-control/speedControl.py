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

def calculate_speeds(hub: float, frequency: int) -> tuple:
    """
    Berechnet forward_speed und backward_speed als Hex-Werte.

    Args:
    - hub (float): Hub in cm (zwischen 0.5 und 3)
    - frequency (int): Frequenz in bpm (zwischen 10 und 125)

    Returns:
    - tuple: (forward_speed_hex, backward_speed_hex, pulse_hex)
    """
    if not (0.5 <= hub <= 3):
        raise ValueError("Hub muss zwischen 0.5 und 3 cm liegen.")
    if not (10 <= frequency <= 125):
        raise ValueError("Frequenz muss zwischen 10 und 125 bpm liegen.")

    # Konstante Werte
    SteigungSpindel = 0.5  # Steigung in cm/Umdrehung
    pulsesPerRotation = 10000  # Pulse pro Umdrehung

    # Berechnungen
    pulse = int(hub / SteigungSpindel * pulsesPerRotation)  # Pulse insgesamt (auf Integer gerundet)
    cycle_time = 60 / frequency  # Zykluszeit für eine Vorwärts- und Rückwärtsbewegung in Sekunden
    sys_time = cycle_time / 3  # Zeit für Vorwärtsbewegung
    dia_time = 2 * cycle_time / 3  # Zeit für Rückwärtsbewegung
    rounds = pulse / pulsesPerRotation  # Anzahl der Umdrehungen

    # Geschwindigkeiten in RPM berechnen
    forward_speed = int((rounds / sys_time) * 60)
    backward_speed = int((rounds / dia_time) * 60)

    # Geschwindigkeiten in Hexadezimal umwandeln
    forward_speed_hex = hex(forward_speed)
    backward_speed_hex = hex(backward_speed)
    pulse_hex = hex(pulse)
    
    #high_pulse_hex = pulse_hex[:4]
    #low_pulse_hex = pulse_hex[4:]
    
    print(f"Systole Speed = {forward_speed_hex}, Diastole Speed {backward_speed_hex}, Pulses = {pulse_hex}")

    return forward_speed, backward_speed, pulse

### SET ONLY MOTOR SPEED ###
def set_motor_speed(frequency: int, hub: float):
    """Calculates and writes new motor speeds based on frequency and stroke."""
    sys_speed, dia_speed, _ = calculate_speeds(hub, frequency)
    write_register(0x621B, sys_speed)  # Update systole speed
    write_register(0x6223, dia_speed)  # Update diastole speed
    print(f" Motor speed updated: Systole={sys_speed} RPM, Diastole={dia_speed} RPM")

### SET ONLY TARGET POSITION ###
def set_motor_position(hub: float):
    """Calculates and writes new target position based on stroke volume."""
    _, _, target_position = calculate_speeds(hub, 60)  # Default frequency (doesn't matter)
    write_register(0x621A, target_position)  # Update target position
    print(f" Motor position updated: Target position = {target_position}")


try:
    sys_speed, dia_speed, target_position = calculate_speeds(2.5,60) #(Hub,Frequenz)
    
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


finally:
    # Close the Modbus connection
    client.close()
    print("Connection closed.")


