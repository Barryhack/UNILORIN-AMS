import serial
import time
from typing import Optional

class RFIDReader:
    def __init__(self, port: str = 'COM3', baudrate: int = 9600):
        """Initialize RFID reader on specified port"""
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False

    def connect(self) -> bool:
        """Establish connection with the RFID reader"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.connected = True
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to RFID reader: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from the RFID reader"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connected = False

    def read_tag(self, timeout: int = 10) -> Optional[str]:
        """
        Read RFID tag and return its ID
        
        Args:
            timeout (int): Maximum time to wait for tag in seconds
            
        Returns:
            str: RFID tag ID if successful, None otherwise
        """
        if not self.connected:
            if not self.connect():
                return None

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.serial.in_waiting:
                try:
                    tag_data = self.serial.readline().decode('utf-8').strip()
                    if tag_data:
                        # Format tag data (remove any unwanted characters)
                        tag_id = ''.join(filter(str.isalnum, tag_data))
                        return tag_id
                except Exception as e:
                    print(f"Error reading RFID tag: {e}")
                    return None
            time.sleep(0.1)
        
        return None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
