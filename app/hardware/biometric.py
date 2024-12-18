import serial
import time
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RFIDReader:
    def __init__(self, port: str = 'COM3', baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None

    def connect(self) -> bool:
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RFID reader: {e}")
            return False

    def read_tag(self) -> Optional[str]:
        """Read RFID tag and return its ID"""
        if not self.serial:
            return None
        
        try:
            if self.serial.in_waiting:
                tag_id = self.serial.readline().decode('utf-8').strip()
                return tag_id
            return None
        except Exception as e:
            logger.error(f"Error reading RFID tag: {e}")
            return None

    def close(self):
        if self.serial:
            self.serial.close()


class FingerprintSensor:
    def __init__(self, port: str = 'COM4', baudrate: int = 57600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None

    def connect(self) -> bool:
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to fingerprint sensor: {e}")
            return False

    def capture_fingerprint(self) -> Optional[Tuple[bytes, int]]:
        """
        Capture fingerprint and return template data and fingerprint ID
        Returns tuple of (template_data, fingerprint_id) or None if failed
        """
        if not self.serial:
            return None

        try:
            # Send command to capture fingerprint
            self.serial.write(b'\xef\x01\xff\xff\xff\xff\x01\x00\x03\x01\x00\x05')
            time.sleep(2)  # Wait for finger placement

            # Read response
            response = self.serial.read(12)
            if len(response) == 12 and response[9] == 0x00:  # Success
                # Get template data
                self.serial.write(b'\xef\x01\xff\xff\xff\xff\x01\x00\x04\x02\x01\x08')
                template_data = self.serial.read(498)  # Typical template size
                
                # Generate unique fingerprint ID
                fingerprint_id = int.from_bytes(template_data[:4], 'big')
                
                return template_data, fingerprint_id
            return None
        except Exception as e:
            logger.error(f"Error capturing fingerprint: {e}")
            return None

    def close(self):
        if self.serial:
            self.serial.close()


# Singleton instances for global access
rfid_reader = RFIDReader()
fingerprint_sensor = FingerprintSensor()
