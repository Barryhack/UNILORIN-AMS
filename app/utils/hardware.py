import requests
import json
from flask import current_app

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
