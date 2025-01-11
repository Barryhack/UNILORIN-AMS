from flask import current_app
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship

class LoginLog(db.Model):
    """Login log model for tracking user login attempts"""
    __tablename__ = 'login_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Made nullable for failed logins
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(50))  # 'login', 'logout', etc.
    status = db.Column(db.String(50))  # 'success', 'failed'
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))  # For storing browser/client information
    details = db.Column(db.String(255))  # For storing additional details about the log entry

    # Relationships
    user = relationship('User', back_populates='login_logs')

    def __init__(self, user_id=None, action='login', status='success', ip_address=None, user_agent=None, details=None):
        self.user_id = user_id
        self.action = action
        self.status = status
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.details = details

    def __repr__(self):
        return f'<LoginLog {self.user_id} - {self.action}:{self.status} at {self.timestamp}>'

    @classmethod
    def log_activity(cls, user_id=None, action='login', status='success', ip_address=None, user_agent=None, details=None):
        """Log a login-related activity"""
        log = cls(
            user_id=user_id,
            action=action,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        db.session.add(log)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error logging login activity: {str(e)}")

    @classmethod
    def get_recent_logs(cls, limit=10):
        """Get recent login logs"""
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()

    @classmethod
    def get_user_logs(cls, user_id, limit=None):
        """Get login logs for a specific user"""
        query = cls.query.filter_by(user_id=user_id).order_by(cls.timestamp.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def get_failed_attempts(cls, ip_address, minutes=15):
        """Get number of failed login attempts from an IP address in the last X minutes"""
        since = datetime.utcnow() - timedelta(minutes=minutes)
        return cls.query.filter(
            cls.ip_address == ip_address,
            cls.status == 'failed',
            cls.timestamp >= since
        ).count()

    @classmethod
    def cleanup_old_logs(cls, days=30):
        """Delete logs older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        try:
            cls.query.filter(cls.timestamp < cutoff).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error cleaning up old login logs: {str(e)}")

    def to_dict(self):
        """Convert login log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'action': self.action,
            'status': self.status,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'details': self.details
        }
