from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship

class ActivityLog(db.Model):
    """Activity log model for tracking user actions"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(10), db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'mark_attendance', 'create_course'
    details = db.Column(db.Text)  # JSON string with action details
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    resource_type = db.Column(db.String(50))  # e.g., 'course', 'attendance', 'user'
    resource_id = db.Column(db.Integer)  # ID of the affected resource
    status = db.Column(db.String(20), default='success')  # success, failed, pending
    error_message = db.Column(db.Text)

    # Relationships
    user = relationship('User', back_populates='activity_logs')

    def __repr__(self):
        return f'<ActivityLog {self.user.username} - {self.action} at {self.timestamp}>'

    def to_dict(self):
        """Convert activity log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'status': self.status,
            'error_message': self.error_message,
            'username': self.user.username if self.user else None
        }

    @classmethod
    def log_activity(cls, user_id, action, details=None, ip_address=None, 
                    resource_type=None, resource_id=None, status='success', 
                    error_message=None):
        """Create a new activity log entry"""
        log = cls(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            error_message=error_message
        )
        db.session.add(log)
        db.session.commit()
        return log

    @classmethod
    def get_user_activities(cls, user_id, limit=None):
        """Get activities for a specific user"""
        query = cls.query.filter_by(user_id=user_id).order_by(cls.timestamp.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def get_resource_activities(cls, resource_type, resource_id):
        """Get activities for a specific resource"""
        return cls.query.filter_by(
            resource_type=resource_type,
            resource_id=resource_id
        ).order_by(cls.timestamp.desc()).all()

    @classmethod
    def get_recent_activities(cls, limit=10):
        """Get recent activities"""
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()

    @classmethod
    def get_activities_by_date_range(cls, start_date, end_date):
        """Get activities within a date range"""
        return cls.query.filter(
            cls.timestamp >= start_date,
            cls.timestamp <= end_date
        ).order_by(cls.timestamp.desc()).all()

    @classmethod
    def get_activities_by_action(cls, action, limit=None):
        """Get activities by action type"""
        query = cls.query.filter_by(action=action).order_by(cls.timestamp.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def get_failed_activities(cls, limit=None):
        """Get failed activities"""
        query = cls.query.filter_by(status='failed').order_by(cls.timestamp.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
