from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import time


#TODO creat a ModbusController class 

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

# Attempt to connect to the RS485 device
connected = client.connect()
if not connected:
    print("Warning: Modbus device not found. Running in offline mode.")
    #exit()

def write_register(address, value):
    """Write a single value to a Modbus register."""
    if not connected:
        print(f"Warning: Modbus offline. Cannot write {hex(value)} to {hex(address)}.")
        return

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
    if not connected:
        print(f"Warning: Modbus offline. Cannot read register {hex(address)}.")
        return None

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
    - tuple: (forward_speed, backward_speed, pulse)
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

    print(f"Systole Speed = {forward_speed}, Diastole Speed {backward_speed}, Pulses = {pulse}")

    return forward_speed, backward_speed, pulse

### SET ONLY MOTOR SPEED ###
def set_motor_speed(frequency: int, hub: float):
    """Calculates and writes new motor speeds based on frequency and stroke."""
    
    #print(f"TESTING: Motor speed function called with Frequency={frequency}, Stroke={hub}")  # Only for testing purposes

    if not connected:
        print("Warning: Modbus offline. Cannot update motor speed.")
        return

    sys_speed, dia_speed, _ = calculate_speeds(hub, frequency)
    
    # Print values before writing to Modbus (For Debugging)
    #print(f"TESTING: Writing Systole Speed = {sys_speed} RPM to 0x621B")  # Only for testing purposes
    #print(f"TESTING: Writing Diastole Speed = {dia_speed} RPM to 0x6223")  # Only for testing purposes

    write_register(0x621B, sys_speed)  # Update systole speed
    write_register(0x6223, dia_speed)  # Update diastole speed
    print(f"Motor speed updated: Systole={sys_speed} RPM, Diastole={dia_speed} RPM")
    
    # Trigger PATH 3 (then automatically PATH 1)
    #write_register(0x6002, 0x0013)
    print(f"Triggering the PATH again")

### SET ONLY TARGET POSITION ###
def set_motor_target_position(frequency: int, hub: float):
    """Calculates and writes new target position based on stroke volume."""

    #print(f"TESTING: Target position function called with Frequency={frequency}, Stroke={hub}")  # Only for testing purposes
    
    if not connected:
        print("Warning: Modbus offline. Cannot update motor position.")
        return

    _, _, target_position = calculate_speeds(hub, frequency)
    #print(f"TESTING: Writing Target Position = {target_position} to 0x621A")  # Only for testing purposes
    
    write_register(0x621A, target_position)  # Update target position
    print(f"Motor position updated: Target position = {target_position}")
    
    # Trigger PATH 3 (then automatically PATH 1)
    #write_register(0x6002, 0x0013)
    print(f"Triggering the PATH again")
    
def start_motor():
    """Start motor."""
    print("TESTING: start_motor() called - Starting the motor...")  # Debug message
    if not connected:
        print("Warning: Modbus offline. Cannot start motor.")
        return
    # Trigger PATH 3 (then automatically PATH 1)
    write_register(0x6002, 0x0013)


def stop_motor():
    """Stops the motor immediately by triggering an emergency stop and disabling the servo."""
    #print("TESTING: stop_motor() called - Stopping the motor!")  # Debug message

    if not connected:
        print("Warning: Modbus offline. Cannot stop motor.")
        return

    write_register(0x6002, 0x0040)  # E-Stop!!
    write_register(0x2009, 0x0001)  # Servo disable

    print("Motor stopped: Emergency stop triggered, servo disabled.")  # Debug message

def reset_motor_position():
    """Resets the motor back to home position. After eneabling the servo (in case its disabled)"""
    
    #print("TESTING: reset_motor_position() called - Resetting the motor position...")  # Debug message

    if not connected:
        print("Warning: Modbus offline. Cannot reset motor position.")
        return
    
    # Enable servo: Write 0 to register 0x2009
    print("Resetting the servo motor...")
    write_register(0x2009, 0x0000)  # Servo enable !! This should be only after the motor was stopped # and the servo was disabled, but doesn't really matter 
    time.sleep(1)
    write_register(0x6002, 0x0040)  # E-Stop!!  This is IMPORTANT for the RESET function!!!
    
    #Probably we only need to trigger the path !! and we dont have to write every time into the register again !!
    # PATH 15 (Last PATH)
    #write_register(0x6278, 0x0011)  # Path15 Mode (dont jump)
    #write_register(0x6279, 0x0000)  # Target position high part (Zero/home)
    #write_register(0x627A, 0x0000)  # Target position low part
    #write_register(0x627B, 0x0032)  # Set speed
    #write_register(0x627C, 0x0032)  # Set acceleration
    #write_register(0x627D, 0x0032)  # Set deceleration
    #time.sleep(1)
    
    # Trigger PATH 15
    write_register(0x6002, 0x001F)

    # Disable servo: Write 1 to register 0x2009 (if needed)
    # print("Disabling the servo motor...")
    #write_register(0x2009, 0x0001)


# Only execute this if Modbus is connected
# TODO ensure that homing is done before running ....... 
if connected:
    try:
        sys_speed, dia_speed, target_position = calculate_speeds(1, 30)  # (Hub, Frequenz)
        
        print(f"Systole Speed = {sys_speed}, Diastole Speed {dia_speed}, Pulses = {target_position}")
        
        #write_register(0x2009, 0x0000)  # Servo enable
        # Path3 
        #write_register(0x6218, 0x4411)  # Path3 Mode (position mode, interrupt, abs position, jump to path1)
        #write_register(0x6219, 0x0000)  # Target position high part
        #write_register(0x621A, target_position)  # Target position low part (30000 steps overall)
        #write_register(0x621B, sys_speed)  # Set speed rpm 
        #write_register(0x621C, 0x0032)  # Set acceleration
        #write_register(0x621D, 0x0032)  # Set deceleration
        #write_register(0x621E, 0x0000)  # Pause time
        
        # PATH 4
        #write_register(0x6220, 0x4311)  # Path4 Mode (jump to Path 3 back)
        #write_register(0x6221, 0x0000)  # Target position high part (Zero/Home)
        #write_register(0x6222, 0x0000)  # Target position low part
        #write_register(0x6223, dia_speed)  # Set speed rpm
        #write_register(0x6224, 0x0032)  # Set acceleration
        #write_register(0x6225, 0x0032)  # Set deceleration
        #write_register(0x6226, 0x0000)  # Pause time
        #time.sleep(1)
        
        # Trigger PATH 3 (then automatically PATH 1)
        #write_register(0x6002, 0x0013)

    finally:
        # Close the Modbus connection
        client.close()
        print("Connection closed.")
