import uasyncio as asyncio
import time

class Ups:
    def __init__(self, uart):
      self.uart = uart
      self.model = ""
      self.serial_number = ""
      self.battery_voltage = 0
      self.line_voltage = 0
      self.load_level = 0
      self.battery_level = 0.0
      self.status = ""
      self.temperature = 0.0
      self.cause_of_transfer = ""
      self.estimated_runtime= 0
      self.self_test_results = ""


    def _send_command(self,cmd):
      self.uart.write(cmd)
      time.sleep(1)
      answer = self.uart.read()
      if answer is not None:
        return (answer.decode()).strip()

    def initialize_smart_mode(self):
      smart_mode = self._send_command(b'Y')
      if smart_mode == "SM":
        return("Smart Mode Initializated")
      else:
        return("Smart Mode Failed to Initialize")
        

    def download_model(self):
      model = self._send_command(b'\x01')
      if model is not None:
        self.model = model
      else:
        self.model = "N/A"
        
    def download_serial_number(self):
      serial = self._send_command(b'n')
      if serial is not None:
        self.serial_number = serial
      else:
        self.serial_number = "N/A"

    def download_battery_voltage(self):
      b_voltage = self._send_command(b'B')
      if b_voltage is not None:
        try:
          self.battery_voltage = float(b_voltage)
        except (ValueError, TypeError):
          self.battery_voltage = 0        
      else:
        self.battery_voltage = 0
        
    def download_line_voltage(self):
      l_voltage = self._send_command(b'L')
      if l_voltage is not None:
        try:
          self.line_voltage = float(l_voltage)
        except (ValueError, TypeError):
          self.line_voltage = 0        
      else:
        self.line_voltage = 0

    def download_load_level(self):
      l_level = self._send_command(b'P')
      if l_level is not None:
        try:
          self.load_level = float(l_level)
        except (ValueError, TypeError):
          self.load_level = 0        
      else:
        self.load_level = 0

    def download_battery_level(self):
      b_level = self._send_command(b'f')
      if b_level is not None:
        try:
          self.battery_level = float(b_level)
        except (ValueError, TypeError):
          self.battery_level = 0        
      else:
        self.battery_level = 0

    def download_status(self):
        status = self._send_command(b'Q')
        if status is not None:
            status_clean = status.strip()
            if len(status_clean) > 2:
                status_clean = status_clean[-2:]
                
            try:
                status_val = int(status_clean, 16)
                if status_val & (1 << 3):
                    self.status = "On-Line"
                elif status_val & (1 << 4):
                    self.status = "On-Battery"
                else:
                    self.status = "Other"
            except ValueError:
                print(f"[UPS] Nieprawidłowa ramka statusu: {repr(status)}")
                self.status = "Error"
        else:
            self.status = "N/A"
        
    def download_temperature(self):
      temperature = self._send_command(b'C')
      if temperature is not None:
        try:
          self.temperature = float(temperature)
        except (ValueError, TypeError):
          self.temperature = 0
      else:
        self.temperature = 0

    def download_cause_of_transfer(self):
      causes={"R":"Unacceptable utility voltage rate of change","H":"High utility voltage","L":"Low utility voltage","T":"line voltage notch or spike","O":"No transfers yet since turnon","S":"Transfer due to U command or activation of UPS test"}
      cause = self._send_command(b'G')
      if cause is not None:
        self.cause_of_transfer = causes.get(cause, "Unknown")
      else:
        self.cause_of_transfer = "N/A"

    def download_estimated_runtime(self):
        runtime = self._send_command(b'j')
        if runtime is not None:
            try:
                # Oczyszczenie z \r\n i usunięcie dwukropka z końca
                cleaned = runtime.strip().rstrip(':')
                self.estimated_runtime = int(cleaned)
            except (ValueError, TypeError):
                self.estimated_runtime = 0
        else:
            self.estimated_runtime = 0

    def do_a_self_test(self):
      results = {"OK":"Battery OK","BT":"Failed due to insufficient capacity","NG":"Failed due to overload","NO":"No results available"}
      execute_test = self._send_command(b'W')
      time.sleep(15)
      if execute_test == "OK":
        test_results = self._send_command(b'X')
        self.self_test_results = results.get(test_results,"Unknown")
      else:
        self.self_test_results = "N/A"

    def simulate_power_failure(self):
      self.uart.write(b'U')
      time.sleep(10)
      power_failure = self.uart.read()
      if power_failure is not None:
        decoded_power_failure = power_failure.decode()
        if "!" in decoded_power_failure and "$" in decoded_power_failure:
          return "Success, UPS back On-Line"
        else:
          return "Error while simulating a power failure"
      else:
        return "Error while simulating a power failure"
      
      
