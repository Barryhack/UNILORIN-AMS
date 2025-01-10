import requests
import logging
from flask import current_app
from enum import Enum
from datetime import datetime
import json

class HardwareMode(Enum):
    IDLE = "idle"
    REGISTRATION = "registration"
    VERIFICATION = "verification"

class HardwareController:
    def __init__(self):
        self.base_url = "http://192.168.4.1"  # Default ESP8266 AP IP
        self.is_connected = False
        self.current_mode = HardwareMode.IDLE
        self.logger = logging.getLogger(__name__)
        self.last_sync = None
        self.status = {
            'fingerprint_ready': False,
            'rfid_ready': False,
            'last_error': None
        }

    def connect(self, ip_address=None):
        """Connect to the ESP8266 by verifying it's accessible"""
        if ip_address:
            self.base_url = f"http://{ip_address}"
        
        try:
            # Try to ping the ESP8266 and get initial status
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                self.is_connected = True
                self.status.update(status_data)
                self.last_sync = datetime.now()
                self.logger.info(f"Connected to ESP8266 at {self.base_url}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to ESP8266: {str(e)}")
            self.is_connected = False
            self.status['last_error'] = str(e)
            return False

    def disconnect(self):
        """Disconnect from the ESP8266"""
        if self.is_connected:
            try:
                requests.post(f"{self.base_url}/disconnect")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {str(e)}")
            finally:
                self.is_connected = False
                self.current_mode = HardwareMode.IDLE
                self.logger.info("Disconnected from ESP8266")

    def set_mode(self, mode: HardwareMode):
        """Set the hardware mode (registration or verification)"""
        if not self.is_connected:
            raise Exception("Hardware not connected")
        
        try:
            response = requests.post(
                f"{self.base_url}/mode",
                json={'mode': mode.value}
            )
            if response.status_code == 200:
                self.current_mode = mode
                self.logger.info(f"Mode set to: {mode.value}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to set mode: {str(e)}")
            self.status['last_error'] = str(e)
            raise

    def start_registration(self, user_id: str):
        """Start registration process for a user"""
        if not self.is_connected:
            raise Exception("Hardware not connected")
        
        try:
            # Set mode to registration and send user ID
            self.set_mode(HardwareMode.REGISTRATION)
            response = requests.post(
                f"{self.base_url}/registration/start",
                json={'user_id': user_id}
            )
            if response.status_code == 200:
                self.logger.info(f"Started registration for user: {user_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to start registration: {str(e)}")
            self.status['last_error'] = str(e)
            raise

    def verify_attendance(self):
        """Start verification process for attendance"""
        if not self.is_connected:
            raise Exception("Hardware not connected")
        
        try:
            # Set mode to verification
            self.set_mode(HardwareMode.VERIFICATION)
            response = requests.post(f"{self.base_url}/verification/start")
            if response.status_code == 200:
                self.logger.info("Started verification process")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to start verification: {str(e)}")
            self.status['last_error'] = str(e)
            raise

    def get_registration_data(self):
        """Get registration data (both RFID and fingerprint)"""
        if not self.is_connected or self.current_mode != HardwareMode.REGISTRATION:
            raise Exception("Hardware not connected or not in registration mode")
        
        try:
            response = requests.get(f"{self.base_url}/registration/data")
            if response.status_code == 200:
                data = response.json()
                return {
                    'rfid_data': data.get('rfid_data'),
                    'fingerprint_data': data.get('fingerprint_data'),
                    'timestamp': data.get('timestamp')
                }
            return None
        except Exception as e:
            self.logger.error(f"Failed to get registration data: {str(e)}")
            self.status['last_error'] = str(e)
            raise

    def get_verification_result(self):
        """Get verification result"""
        if not self.is_connected or self.current_mode != HardwareMode.VERIFICATION:
            raise Exception("Hardware not connected or not in verification mode")
        
        try:
            response = requests.get(f"{self.base_url}/verification/result")
            if response.status_code == 200:
                result = response.json()
                return {
                    'verified': result.get('verified', False),
                    'user_id': result.get('user_id'),
                    'timestamp': result.get('timestamp'),
                    'method': result.get('method')  # 'rfid' or 'fingerprint'
                }
            return None
        except Exception as e:
            self.logger.error(f"Failed to get verification result: {str(e)}")
            self.status['last_error'] = str(e)
            raise

    def get_status(self):
        """Get current hardware status"""
        if not self.is_connected:
            return {
                'connected': False,
                'mode': HardwareMode.IDLE.value,
                'fingerprint_ready': False,
                'rfid_ready': False,
                'last_sync': None,
                'last_error': self.status['last_error']
            }
        
        try:
            response = requests.get(f"{self.base_url}/status")
            if response.status_code == 200:
                status_data = response.json()
                self.status.update(status_data)
                self.last_sync = datetime.now()
            return {
                'connected': self.is_connected,
                'mode': self.current_mode.value,
                'fingerprint_ready': self.status['fingerprint_ready'],
                'rfid_ready': self.status['rfid_ready'],
                'last_sync': self.last_sync,
                'last_error': self.status['last_error']
            }
        except Exception as e:
            self.logger.error(f"Failed to get status: {str(e)}")
            self.status['last_error'] = str(e)
            return {
                'connected': self.is_connected,
                'mode': self.current_mode.value,
                'fingerprint_ready': False,
                'rfid_ready': False,
                'last_sync': self.last_sync,
                'last_error': str(e)
            }

    def reset(self):
        """Reset the hardware to idle mode"""
        if self.is_connected:
            try:
                response = requests.post(f"{self.base_url}/reset")
                if response.status_code == 200:
                    self.current_mode = HardwareMode.IDLE
                    self.logger.info("Hardware reset successful")
                    return True
                return False
            except Exception as e:
                self.logger.error(f"Failed to reset hardware: {str(e)}")
                self.status['last_error'] = str(e)
                raise

# Create a global instance
controller = HardwareController()
