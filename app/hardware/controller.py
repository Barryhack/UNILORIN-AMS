import requests
import logging
from flask import current_app

class HardwareController:
    def __init__(self):
        self.base_url = "http://192.168.4.1"  # Default ESP8266 AP IP
        self.is_connected = False
        self.registration_mode = False
        self.logger = logging.getLogger(__name__)

    def connect(self, ip_address=None):
        """Connect to the ESP8266 by verifying it's accessible"""
        if ip_address:
            self.base_url = f"http://{ip_address}"
        
        try:
            # Try to ping the ESP8266
            response = requests.get(f"{self.base_url}/ping", timeout=5)
            if response.status_code == 200:
                self.is_connected = True
                self.logger.info(f"Connected to ESP8266 at {self.base_url}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to ESP8266: {str(e)}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from the ESP8266"""
        self.is_connected = False
        self.registration_mode = False
        self.logger.info("Disconnected from ESP8266")

    def enable_registration(self):
        """Enable registration mode on the ESP8266"""
        if not self.is_connected:
            raise Exception("Hardware not connected")
        
        try:
            response = requests.post(f"{self.base_url}/registration/enable")
            if response.status_code == 200:
                self.registration_mode = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to enable registration mode: {str(e)}")
            raise

    def disable_registration(self):
        """Disable registration mode on the ESP8266"""
        if not self.is_connected:
            raise Exception("Hardware not connected")
        
        try:
            response = requests.post(f"{self.base_url}/registration/disable")
            if response.status_code == 200:
                self.registration_mode = False
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to disable registration mode: {str(e)}")
            raise

    def get_rfid_data(self):
        """Get the last scanned RFID data"""
        if not self.is_connected or not self.registration_mode:
            raise Exception("Hardware not connected or registration mode not active")
        
        try:
            response = requests.get(f"{self.base_url}/rfid/data")
            if response.status_code == 200:
                return response.json().get('rfid_data')
            return None
        except Exception as e:
            self.logger.error(f"Failed to get RFID data: {str(e)}")
            raise

    def get_fingerprint_data(self):
        """Get the last scanned fingerprint data"""
        if not self.is_connected or not self.registration_mode:
            raise Exception("Hardware not connected or registration mode not active")
        
        try:
            response = requests.get(f"{self.base_url}/fingerprint/data")
            if response.status_code == 200:
                return response.json().get('fingerprint_data')
            return None
        except Exception as e:
            self.logger.error(f"Failed to get fingerprint data: {str(e)}")
            raise

# Create a global instance
controller = HardwareController()
