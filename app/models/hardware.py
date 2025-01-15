from datetime import datetime
from app.extensions import db

class HardwareStatus(db.Model):
    """Model for hardware status tracking."""
    
    __tablename__ = 'hardware_status'
    
    id = db.Column(db.Integer, primary_key=True)
    controller_connected = db.Column(db.Boolean, default=False)
    fingerprint_ready = db.Column(db.Boolean, default=False)
    rfid_ready = db.Column(db.Boolean, default=False)
    display_ready = db.Column(db.Boolean, default=False)
    battery_level = db.Column(db.Integer, default=0)
    charging = db.Column(db.Boolean, default=False)
    current_port = db.Column(db.String(50))
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self):
        self.last_update = datetime.utcnow()
    
    def update_status(self, status_dict):
        """Update status from dictionary."""
        self.controller_connected = status_dict.get('connected', False)
        self.fingerprint_ready = status_dict.get('fingerprint', False)
        self.rfid_ready = status_dict.get('rfid', False)
        self.display_ready = status_dict.get('display', False)
        self.battery_level = status_dict.get('battery', 0)
        self.charging = status_dict.get('charging', False)
        self.current_port = status_dict.get('port')
        self.last_update = datetime.utcnow()
    
    def to_dict(self):
        """Convert status to dictionary."""
        return {
            'connected': self.controller_connected,
            'fingerprint': self.fingerprint_ready,
            'rfid': self.rfid_ready,
            'display': self.display_ready,
            'battery': self.battery_level,
            'charging': self.charging,
            'port': self.current_port,
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
