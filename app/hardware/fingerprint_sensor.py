import serial
import time
from typing import Optional, Tuple
import hashlib

class FingerprintSensor:
    def __init__(self, port: str = 'COM4', baudrate: int = 57600):
        """Initialize fingerprint sensor on specified port"""
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False

    def connect(self) -> bool:
        """Establish connection with the fingerprint sensor"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.connected = True
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to fingerprint sensor: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from the fingerprint sensor"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connected = False

    def capture_fingerprint(self, timeout: int = 30) -> Optional[Tuple[bytes, str]]:
        """
        Capture fingerprint and return its template and hash
        
        Args:
            timeout (int): Maximum time to wait for fingerprint in seconds
            
        Returns:
            Tuple[bytes, str]: Tuple of (template data, template hash) if successful,
                             None otherwise
        """
        if not self.connected:
            if not self.connect():
                return None

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.serial.in_waiting:
                try:
                    # Read raw template data
                    template_data = self.serial.read(self.serial.in_waiting)
                    if template_data:
                        # Generate a hash of the template for storage/comparison
                        template_hash = hashlib.sha256(template_data).hexdigest()
                        return (template_data, template_hash)
                except Exception as e:
                    print(f"Error capturing fingerprint: {e}")
                    return None
            time.sleep(0.1)
        
        return None

    def verify_fingerprint(self, stored_template: bytes, timeout: int = 10) -> bool:
        """
        Verify a captured fingerprint against a stored template
        
        Args:
            stored_template (bytes): Previously stored template to compare against
            timeout (int): Maximum time to wait for fingerprint in seconds
            
        Returns:
            bool: True if fingerprint matches, False otherwise
        """
        if not self.connected:
            if not self.connect():
                return False

        result = self.capture_fingerprint(timeout)
        if result:
            captured_template, _ = result
            # Compare templates using sensor's matching algorithm
            # This is a simplified example - actual implementation would use
            # the sensor's specific matching commands
            return captured_template == stored_template
        
        return False

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
