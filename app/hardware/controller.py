"""Hardware controller module for managing fingerprint and RFID devices."""
import logging
import serial
import time
import os
from threading import Lock
from typing import Optional, Dict, Any, Tuple
from ..models import User
from ..extensions import db

logger = logging.getLogger(__name__)

class HardwareController:
    """Controller for managing fingerprint and RFID hardware."""
    
    def __init__(self, port: str = 'COM3', baudrate: int = 9600, simulation_mode: bool = False):
        """Initialize the hardware controller.
        
        Args:
            port: Serial port for the hardware
            baudrate: Baud rate for serial communication
            simulation_mode: Flag to enable simulation mode
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.lock = Lock()
        self.connected = False
        self.last_error = None
        self.simulation_mode = simulation_mode
        
        if not self.simulation_mode:
            try:
                self.connect()
            except Exception as e:
                logger.error(f"Failed to initialize hardware: {e}")
                self.last_error = str(e)
    
    def connect(self) -> bool:
        """Establish connection with the hardware."""
        if self.simulation_mode:
            logger.info("Running in simulation mode - hardware connection simulated")
            self.connected = True
            return True
            
        try:
            with self.lock:
                if not self.connected:
                    self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
                    time.sleep(2)  # Wait for hardware initialization
                    self.connected = True
                    logger.info("Successfully connected to hardware")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to hardware: {e}")
            self.last_error = str(e)
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the hardware."""
        if self.simulation_mode:
            logger.info("Running in simulation mode - hardware disconnection simulated")
            self.connected = False
            return
            
        try:
            with self.lock:
                if self.serial and self.serial.is_open:
                    self.serial.close()
                self.connected = False
        except Exception as e:
            logger.error(f"Error disconnecting from hardware: {e}")
            self.last_error = str(e)
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the hardware.
        
        Returns:
            Dict containing status information
        """
        if self.simulation_mode:
            return {
                'connected': self.connected,
                'port': 'SIMULATED',
                'mode': 'simulation',
                'last_error': self.last_error
            }
            
        return {
            'connected': self.connected,
            'port': self.port,
            'mode': 'hardware',
            'last_error': self.last_error
        }
    
    def scan_fingerprint(self) -> Tuple[bool, Optional[bytes], str]:
        """Scan a fingerprint.
        
        Returns:
            Tuple of (success, template_data, message)
        """
        if self.simulation_mode:
            logger.info("Running in simulation mode - fingerprint scan simulated")
            return True, b'SIMULATED_FINGERPRINT_TEMPLATE', "Fingerprint scanned successfully"
        
        try:
            with self.lock:
                if not self.connected:
                    if not self.connect():
                        return False, None, "Hardware not connected"
                
                # Send fingerprint scan command
                self.serial.write(b'SCAN_FINGERPRINT\n')
                response = self.serial.readline().decode().strip()
                
                if response.startswith('SUCCESS'):
                    # Extract template data from response
                    template_data = bytes.fromhex(response.split(':')[1])
                    return True, template_data, "Fingerprint scanned successfully"
                else:
                    return False, None, response
        except Exception as e:
            logger.error(f"Error scanning fingerprint: {e}")
            self.last_error = str(e)
            return False, None, f"Error scanning fingerprint: {e}"
    
    def scan_rfid(self) -> Tuple[bool, Optional[str], str]:
        """Scan an RFID card.
        
        Returns:
            Tuple of (success, card_id, message)
        """
        if self.simulation_mode:
            logger.info("Running in simulation mode - RFID scan simulated")
            return True, 'SIMULATED_RFID_CARD_ID', "RFID card scanned successfully"
        
        try:
            with self.lock:
                if not self.connected:
                    if not self.connect():
                        return False, None, "Hardware not connected"
                
                # Send RFID scan command
                self.serial.write(b'SCAN_RFID\n')
                response = self.serial.readline().decode().strip()
                
                if response.startswith('SUCCESS'):
                    # Extract card ID from response
                    card_id = response.split(':')[1]
                    return True, card_id, "RFID card scanned successfully"
                else:
                    return False, None, response
        except Exception as e:
            logger.error(f"Error scanning RFID card: {e}")
            self.last_error = str(e)
            return False, None, f"Error scanning RFID card: {e}"
    
    def register_user(self) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Register a new user by scanning both fingerprint and RFID.
        
        Returns:
            Tuple of (success, registration_data, message)
        """
        if self.simulation_mode:
            logger.info("Running in simulation mode - user registration simulated")
            registration_data = {
                'fingerprint_template': 'SIMULATED_FINGERPRINT_TEMPLATE',
                'rfid_card_id': 'SIMULATED_RFID_CARD_ID'
            }
            return True, registration_data, "Registration successful"
        
        try:
            # Step 1: Scan fingerprint
            fp_success, fp_template, fp_message = self.scan_fingerprint()
            if not fp_success:
                return False, None, f"Fingerprint scan failed: {fp_message}"
            
            # Step 2: Scan RFID
            rfid_success, card_id, rfid_message = self.scan_rfid()
            if not rfid_success:
                return False, None, f"RFID scan failed: {rfid_message}"
            
            # Return combined data
            registration_data = {
                'fingerprint_template': fp_template.hex(),
                'rfid_card_id': card_id
            }
            
            return True, registration_data, "Registration successful"
            
        except Exception as e:
            logger.error(f"Error during user registration: {e}")
            self.last_error = str(e)
            return False, None, f"Registration failed: {e}"
    
    def verify_user(self, user_id: int) -> Tuple[bool, str]:
        """Verify a user's identity using both fingerprint and RFID.
        
        Args:
            user_id: ID of the user to verify
            
        Returns:
            Tuple of (success, message)
        """
        if self.simulation_mode:
            logger.info("Running in simulation mode - user verification simulated")
            return True, "User verified successfully"
        
        try:
            # Get user data
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Step 1: Scan fingerprint
            fp_success, fp_template, fp_message = self.scan_fingerprint()
            if not fp_success:
                return False, f"Fingerprint verification failed: {fp_message}"
            
            # Step 2: Scan RFID
            rfid_success, card_id, rfid_message = self.scan_rfid()
            if not rfid_success:
                return False, f"RFID verification failed: {rfid_message}"
            
            # Verify fingerprint template
            if fp_template.hex() != user.fingerprint_template:
                return False, "Fingerprint does not match"
            
            # Verify RFID card
            if card_id != user.rfid_card_id:
                return False, "RFID card does not match"
            
            return True, "User verified successfully"
            
        except Exception as e:
            logger.error(f"Error during user verification: {e}")
            self.last_error = str(e)
            return False, f"Verification failed: {e}"

# Global hardware controller instance
controller = None

def init_hardware(port: str = 'COM3', baudrate: int = 9600) -> None:
    """Initialize the global hardware controller.
    
    Args:
        port: Serial port for the hardware
        baudrate: Baud rate for serial communication
    """
    global controller
    try:
        controller = HardwareController(port, baudrate)
        logger.info("Hardware controller initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize hardware controller: {e}")
        controller = HardwareController(port, baudrate, simulation_mode=True)
        logger.info("Falling back to simulation mode")

def get_hardware_controller() -> Optional[HardwareController]:
    """Get the global hardware controller instance.
    
    Returns:
        The hardware controller instance or None if not initialized
    """
    global controller
    if controller is None:
        try:
            init_hardware()
        except Exception as e:
            logger.error(f"Error getting hardware controller: {e}")
            return None
    return controller
