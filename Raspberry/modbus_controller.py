# This the new ModbusController CLASS code !

from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import time

class ModbusController:
    def __init__(self, port='/dev/com2', baudrate=115200):
        # Configure Modbus RTU connection
        self.client = ModbusClient(
            method='rtu',
            port=port,
            baudrate=baudrate,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=1
        )
        # Attempt to connect to the RS485 device
        self.connected = self.client.connect()
        if not self.connected:
            print("Warning: Modbus device not found. Running in offline mode.")

            # here should the RECONNECTING LOOP take place

    def write_register(self, address, value):
        """Write a single value to a Modbus register."""
        if not self.connected:
            print(f"Warning: Modbus offline. Cannot write {hex(value)} to {hex(address)}.")
            return

        try:
            result = self.client.write_register(address, value, unit=1)
            if result.isError():
                print(f"Failed to write to register {hex(address)}")
            else:
                print(f"Successfully wrote {hex(value)} to register {hex(address)}")
        except Exception as e:
            print(f"Error: {e}")

    def read_register(self, address):
        """Read a single value from a Modbus register."""
        if not self.connected:
            #print(f"Warning: Modbus offline. Cannot read register {hex(address)}.")
            return None

        try:
            result = self.client.read_holding_registers(address, 1, unit=1)
            if result.isError():
                print(f"Failed to read register {hex(address)}")
            else:
                value = result.registers[0]
                print(f"Value at register {hex(address)}: {hex(value)}")
                return value
        except Exception as e:
            print(f"Error: {e}")
            return None

    def calculate_speeds(self, hub: float, frequency: int) -> tuple:
        """
        Berechnet forward_speed und backward_speed als Hex-Werte.

        Args:
        - hub (float): Hub in cm (zwischen 0.5 und 3)
        - frequency (int): Frequenz in bpm (zwischen 10 und 125)

        Returns:
        - tuple: (forward_speed, backward_speed, pulse)
        """
        if not (0.5 <= hub <= 3):           # No higher or lower values can be entered anyways! 
            raise ValueError("Hub muss zwischen 0.5 und 3 cm liegen.")
        if not (10 <= frequency <= 125):
            raise ValueError("Frequeny muss zwischen 10 und 125 bpm liegen.")

        # Konstante Werte
        SteigungSpindel = 0.5  # Steigung in cm/Umdrehung
        pulsesPerRotation = 10000  # Pulse pro Umdrehung

        # Berechnungen
        pulse = int(hub / SteigungSpindel * pulsesPerRotation)
        cycle_time = 60 / frequency
        sys_time = cycle_time / 3
        dia_time = 2 * cycle_time / 3
        rounds = pulse / pulsesPerRotation

        forward_speed = int((rounds / sys_time) * 60)
        backward_speed = int((rounds / dia_time) * 60)

        #print(f"Systole Speed = {forward_speed}, Diastole Speed {backward_speed}, Pulses = {pulse}") # Debug message
        return forward_speed, backward_speed, pulse

    def set_motor_speed(self, frequency: int, hub: float):
        """Calculates and writes new motor speeds based on frequency and stroke."""
        if not self.connected:
            #print("Warning: Modbus offline. Cannot update motor speed.")
            return

        sys_speed, dia_speed, _ = self.calculate_speeds(hub, frequency)
        self.write_register(0x621B, sys_speed)  # Update systole speed
        self.write_register(0x6223, dia_speed)  # Update diastole speed
        #print(f"Motor speed updated: Systole={sys_speed} RPM, Diastole={dia_speed} RPM")
        #print(f"Triggering the PATH again")

    def set_motor_target_position(self, frequency: int, hub: float):
        """Calculates and writes new target position based on stroke volume."""
        if not self.connected:
            #print("Warning: Modbus offline. Cannot update motor position.")
            return

        _, _, target_position = self.calculate_speeds(hub, frequency)
        self.write_register(0x621A, target_position)  # Update target position
        #print(f"Motor position updated: Target position = {target_position}")
        #print(f"Triggering the PATH again")

    def start_motor(self):
        """Start motor."""
        #print("TESTING: start_motor() called - Starting the motor...")
        if not self.connected:
            #print("Warning: Modbus offline. Cannot start motor.") #debug message
            return
        self.write_register(0x6002, 0x0013)

    def stop_motor(self):
        """Stops the motor immediately by triggering an emergency stop and disabling the servo."""
        if not self.connected:
            #print("Warning: Modbus offline. Cannot stop motor.") #debug message
            return

        self.write_register(0x6002, 0x0040)  # E-Stop
        self.write_register(0x2009, 0x0001)  # Servo disable
        #print("Motor stopped: Emergency stop triggered, servo disabled.") #debug message

    def reset_motor_position(self):
        """Resets the motor back to home position. After enabling the servo (in case it's disabled)."""
        if not self.connected:
            print("Warning: Modbus offline. Cannot reset motor position.")
            return

        print("Resetting the servo motor...")
        self.write_register(0x2009, 0x0000)  # Servo enable
        time.sleep(1)
        self.write_register(0x6002, 0x0040)  # E-Stop
        self.write_register(0x6002, 0x001F)  # Trigger PATH 15 (home)

    def close(self):
        """Closes the Modbus connection cleanly."""
        self.client.close()
        print("Connection closed.")
