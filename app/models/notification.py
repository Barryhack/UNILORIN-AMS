from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from datetime import timedelta

class Notification(db.Model):
    """Notification model for managing user notifications"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(10), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, warning, error, success
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    link = db.Column(db.String(255))  # Optional link to related content
    source = db.Column(db.String(50))  # system, attendance, course, etc.
    priority = db.Column(db.Integer, default=0)  # 0=normal, 1=important, 2=urgent

    # Relationships
    user = relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.title} for {self.user.username}>'

    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'link': self.link,
            'source': self.source,
            'priority': self.priority
        }

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()

    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            db.session.commit()

    @classmethod
    def create_notification(cls, user_id, title, message, type='info', link=None, 
                          source='system', priority=0):
        """Create a new notification"""
        notification = cls(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            link=link,
            source=source,
            priority=priority
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @classmethod
    def get_unread_count(cls, user_id):
        """Get count of unread notifications for a user"""
        return cls.query.filter_by(user_id=user_id, is_read=False).count()

    @classmethod
    def get_user_notifications(cls, user_id, limit=None, unread_only=False):
        """Get notifications for a user"""
        query = cls.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        query = query.order_by(cls.priority.desc(), cls.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def mark_all_as_read(cls, user_id):
        """Mark all notifications as read for a user"""
        notifications = cls.query.filter_by(user_id=user_id, is_read=False).all()
        for notification in notifications:
            notification.mark_as_read()
        db.session.commit()

    @classmethod
    def delete_old_notifications(cls, days=30):
        """Delete notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cls.query.filter(cls.created_at < cutoff_date).delete()
        db.session.commit()

    @classmethod
    def get_notifications_by_source(cls, user_id, source, limit=None):
        """Get notifications by source"""
        query = cls.query.filter_by(user_id=user_id, source=source)
        query = query.order_by(cls.priority.desc(), cls.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    def delete(self):
        """Delete the notification"""
        db.session.delete(self)
        db.session.commit()
