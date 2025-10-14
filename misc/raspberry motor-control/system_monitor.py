# system_monitor.py

from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from register_maps import REGISTER_CATEGORIES 

class SystemMonitor:
    def __init__(self, port='/dev/com2', baudrate=115200, unit_id=1):
        self.client = ModbusClient(
            method='rtu',
            port=port,
            baudrate=baudrate,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=1
        )
        self.unit_id = unit_id

        if not self.client.connect():
            raise ConnectionError("Failed to connect to the Modbus device.")

    def read_register(self, address):
        try:
            result = self.client.read_holding_registers(address, 1, unit=self.unit_id)
            if result.isError():
                return None
            return result.registers[0]
        except Exception:
            return None

    def check_registers(self, category_name, register_map):
        """
        Check a set of registers against expected values.
        Args:
            category_name (str): Just for printing.
            register_map (dict): {address: expected_value}
        Returns:
            bool: True if all matched, False otherwise
        """
        mismatch_found = False
        for address, expected in register_map.items():
            value = self.read_register(address)
            if value is None or value != expected:
                mismatch_found = True
                print(f"[MISMATCH] {hex(address)}: read={hex(value) if value else 'None'}, expected={hex(expected)}")
        if not mismatch_found:
            print(f"[{category_name}] check passed.")
        return not mismatch_found
    

if __name__ == "__main__":
    monitor = SystemMonitor()

    monitor.check_registers("startup", REGISTER_CATEGORIES["startup"])
    monitor.check_registers("homing_check", REGISTER_CATEGORIES["homing_check"])
    monitor.check_registers("alarm_status", REGISTER_CATEGORIES["alarm_status"])
