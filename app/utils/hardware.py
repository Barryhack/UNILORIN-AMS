import requests
import json
import serial
import time
from flask import current_app
from threading import Lock

class HardwareController:
    """Controller class for managing the NodeMCU-based attendance system hardware."""
    
    def __init__(self):
        self._serial_port = None
        self._port_name = None
        self._connected = False
        self._lock = Lock()
        self._last_status = {
            'battery': 0,
            'charging': False,
            'fingerprint': False,
            'rfid': False,
            'display': False
        }
        
    def connect(self, port_name, baudrate=115200):
        """
        Connect to the NodeMCU through serial port.
        
        Args:
            port_name (str): Serial port name
            baudrate (int): Baud rate for serial communication
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self._lock:
                if self._connected:
                    return True
                
                self._serial_port = serial.Serial(port_name, baudrate, timeout=1)
                time.sleep(2)  # Wait for connection to stabilize
                
                # Test connection and get initial status
                self._serial_port.write(b'STATUS\n')
                response = self._serial_port.readline().decode().strip()
                
                if response.startswith('STATUS:'):
                    self._connected = True
                    self._port_name = port_name
                    self._parse_status(response)
                    return True
                else:
                    self._serial_port.close()
                    self._serial_port = None
                    return False
                    
        except Exception as e:
            current_app.logger.error(f"Error connecting to NodeMCU: {e}")
            if self._serial_port:
                self._serial_port.close()
                self._serial_port = None
            return False
    
    def disconnect(self):
        """Disconnect from the NodeMCU."""
        with self._lock:
            if self._serial_port:
                self._serial_port.write(b'DISCONNECT\n')  # Notify device we're disconnecting
                time.sleep(0.1)  # Give device time to process
                self._serial_port.close()
            self._serial_port = None
            self._connected = False
            self._last_status = {
                'battery': 0,
                'charging': False,
                'fingerprint': False,
                'rfid': False,
                'display': False
            }
    
    def is_connected(self):
        """Check if NodeMCU is connected."""
        return self._connected
    
    def get_port(self):
        """Get current serial port name."""
        return self._port_name
    
    def fingerprint_status(self):
        """Get fingerprint sensor status."""
        return self._last_status.get('fingerprint', False)
    
    def rfid_status(self):
        """Get RFID reader status."""
        return self._last_status.get('rfid', False)
    
    def get_status(self):
        """Get complete hardware status."""
        return {
            'connected': self._connected,
            'port': self._port_name,
            'battery': self._last_status.get('battery', 0),
            'charging': self._last_status.get('charging', False),
            'fingerprint': self._last_status.get('fingerprint', False),
            'rfid': self._last_status.get('rfid', False),
            'display': self._last_status.get('display', False)
        }
    
    def _parse_status(self, status_str):
        """Parse status string from NodeMCU."""
        try:
            # Expected format: STATUS:battery=75,charging=1,fp=1,rfid=1,display=1
            parts = status_str.replace('STATUS:', '').split(',')
            for part in parts:
                key, value = part.split('=')
                if key == 'battery':
                    self._last_status['battery'] = int(value)
                elif key == 'charging':
                    self._last_status['charging'] = value == '1'
                elif key == 'fp':
                    self._last_status['fingerprint'] = value == '1'
                elif key == 'rfid':
                    self._last_status['rfid'] = value == '1'
                elif key == 'display':
                    self._last_status['display'] = value == '1'
        except Exception as e:
            current_app.logger.error(f"Error parsing status string: {e}")
    
    def send_command(self, command):
        """
        Send a command to the NodeMCU.
        
        Args:
            command (str): Command to send
            
        Returns:
            tuple: (success, response)
        """
        if not self._connected:
            return False, "Not connected"
            
        try:
            with self._lock:
                self._serial_port.write(f"{command}\n".encode())
                response = self._serial_port.readline().decode().strip()
                return True, response
        except Exception as e:
            current_app.logger.error(f"Error sending command: {e}")
            return False, str(e)
    
    def display_message(self, message, line=1):
        """
        Display a message on the OLED screen.
        
        Args:
            message (str): Message to display
            line (int): Line number (1-4)
            
        Returns:
            bool: Success status
        """
        success, response = self.send_command(f"DISPLAY:{line}:{message}")
        return success and response == "OK"
    
    def clear_display(self):
        """Clear the OLED display."""
        success, response = self.send_command("CLEAR_DISPLAY")
        return success and response == "OK"
    
    def start_fingerprint_enrollment(self):
        """
        Start fingerprint enrollment process.
        
        Returns:
            bool: Success status
        """
        success, response = self.send_command("ENROLL_FP")
        return success and response == "READY"
    
    def start_rfid_enrollment(self):
        """
        Start RFID card enrollment process.
        
        Returns:
            bool: Success status
        """
        success, response = self.send_command("ENROLL_RFID")
        return success and response == "READY"
    
    def cancel_enrollment(self):
        """Cancel any ongoing enrollment process."""
        success, response = self.send_command("CANCEL")
        return success and response == "OK"

    def set_mode(self, mode, **kwargs):
        """
        Set the operating mode of the NodeMCU device.
        
        Args:
            mode (str): Operating mode ('REGISTRATION', 'VERIFICATION', 'DELETE')
            **kwargs: Additional parameters specific to the mode
        
        Returns:
            bool: Success status
        """
        command = f"MODE:{mode}"
        if kwargs:
            params = ','.join(f"{k}={v}" for k, v in kwargs.items())
            command += f":{params}"
        success, response = self.send_command(command)
        return success and response == "OK"

    def start_registration(self):
        """
        Start the registration process for a new user.
        
        This process involves:
        1. Setting registration mode
        2. Getting new ID from server
        3. Waiting for RFID tag
        4. Registering fingerprint
        
        Returns:
            tuple: (success, user_id or error message)
        """
        try:
            # Set registration mode
            if not self.set_mode('REGISTRATION'):
                return False, "Failed to set registration mode"

            # Get new ID from server
            success, response = self.send_command("GET_NEW_ID")
            if not success:
                return False, "Failed to get new ID from server"
            
            user_id = response.strip()
            
            # Wait for RFID registration
            success, response = self.send_command("WAIT_RFID")
            if not success or response != "RFID_OK":
                return False, "RFID registration failed"
            
            # Start fingerprint enrollment
            success, response = self.send_command("ENROLL_FP")
            if not success or response != "FP_OK":
                return False, "Fingerprint enrollment failed"
            
            return True, user_id

        except Exception as e:
            current_app.logger.error(f"Registration error: {e}")
            return False, str(e)

    def verify_user(self):
        """
        Verify a user through RFID and fingerprint.
        
        This process involves:
        1. Setting verification mode
        2. Reading RFID tag
        3. Verifying fingerprint
        4. Getting user details from server
        
        Returns:
            tuple: (success, user_data or error message)
        """
        try:
            # Set verification mode
            if not self.set_mode('VERIFICATION'):
                return False, "Failed to set verification mode"
            
            # Wait for RFID tag
            success, response = self.send_command("WAIT_RFID")
            if not success:
                return False, "RFID read failed"
            
            rfid_data = response.strip()
            
            # Verify fingerprint
            success, response = self.send_command("VERIFY_FP")
            if not success or response != "FP_MATCH":
                return False, "Fingerprint verification failed"
            
            # Get user details from server
            success, response = self.send_command(f"GET_USER:{rfid_data}")
            if not success:
                return False, "Failed to get user details"
            
            try:
                user_data = json.loads(response)
                return True, user_data
            except json.JSONDecodeError:
                return False, "Invalid user data format"

        except Exception as e:
            current_app.logger.error(f"Verification error: {e}")
            return False, str(e)

    def delete_user(self, user_id):
        """
        Delete a user from the system.
        
        Args:
            user_id (str): ID of the user to delete
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Set delete mode
            if not self.set_mode('DELETE', user_id=user_id):
                return False, "Failed to set delete mode"
            
            # Send delete command
            success, response = self.send_command(f"DELETE_USER:{user_id}")
            if not success:
                return False, "Delete operation failed"
            
            return True, "User deleted successfully"

        except Exception as e:
            current_app.logger.error(f"Delete error: {e}")
            return False, str(e)

    def record_attendance(self, user_data, course_id):
        """
        Record attendance for a verified user.
        
        Args:
            user_data (dict): Verified user data
            course_id (str): ID of the course
            
        Returns:
            tuple: (success, message)
        """
        try:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            command = f"RECORD_ATTENDANCE:{user_data['id']},{course_id},{timestamp}"
            success, response = self.send_command(command)
            
            if success:
                # Display success message on OLED
                self.display_message(f"Welcome {user_data['name']}", 1)
                self.display_message(f"Attendance recorded", 2)
                time.sleep(2)  # Show message for 2 seconds
                self.clear_display()
                return True, "Attendance recorded successfully"
            else:
                return False, "Failed to record attendance"

        except Exception as e:
            current_app.logger.error(f"Attendance recording error: {e}")
            return False, str(e)

def send_to_esp8266(endpoint, data):
    """
    Send a request to the ESP8266 device.
    
    Args:
        endpoint (str): The endpoint to send the request to
        data (dict): The data to send in the request body
    
    Returns:
        dict: The response from the ESP8266 device
    """
    try:
        esp8266_ip = current_app.config.get('ESP8266_IP', '192.168.1.100')
        esp8266_port = current_app.config.get('ESP8266_PORT', 80)
        base_url = f"http://{esp8266_ip}:{esp8266_port}"
        
        url = f"{base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, json=data, headers=headers, timeout=5)
        response.raise_for_status()
        
        return {'success': True, 'data': response.json()}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': f"Unexpected error: {str(e)}"}
