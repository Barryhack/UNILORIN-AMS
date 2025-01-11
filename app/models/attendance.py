from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship

class Attendance(db.Model):
    """Attendance model for tracking user attendance"""
    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='present')  # present, absent, late
    marked_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # if marked by lecturer/admin
    verification_method = db.Column(db.String(20))  # fingerprint, rfid, manual
    verification_data = db.Column(db.Text)  # JSON string with verification details
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lecture = relationship('Lecture', back_populates='attendances')
    user = relationship('User', foreign_keys=[user_id], back_populates='attendances')
    marked_by = relationship('User', foreign_keys=[marked_by_id], back_populates='marked_attendances')

    def __repr__(self):
        return f'<Attendance {self.user.name} - {self.lecture.title}>'

    def to_dict(self):
        """Convert attendance record to dictionary"""
        return {
            'id': self.id,
            'lecture_id': self.lecture_id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'marked_by_id': self.marked_by_id,
            'verification_method': self.verification_method,
            'verification_data': self.verification_data,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user': self.user.to_dict() if self.user else None,
            'lecture': {
                'id': self.lecture.id,
                'title': self.lecture.title,
                'course': {
                    'id': self.lecture.course.id,
                    'code': self.lecture.course.code,
                    'title': self.lecture.course.title
                } if self.lecture.course else None
            } if self.lecture else None,
            'marked_by': self.marked_by.to_dict() if self.marked_by else None
        }

    @classmethod
    def mark_attendance(cls, lecture_id, user_id, status='present', marked_by_id=None, 
                       verification_method='manual', verification_data=None, notes=None):
        """Mark attendance for a user"""
        attendance = cls(
            lecture_id=lecture_id,
            user_id=user_id,
            status=status,
            marked_by_id=marked_by_id,
            verification_method=verification_method,
            verification_data=verification_data,
            notes=notes
        )
        db.session.add(attendance)
        db.session.commit()
        return attendance

    @classmethod
    def get_user_attendance(cls, user_id, lecture_id=None):
        """Get attendance records for a user"""
        query = cls.query.filter_by(user_id=user_id)
        if lecture_id:
            query = query.filter_by(lecture_id=lecture_id)
        return query.order_by(cls.timestamp.desc()).all()

    @classmethod
    def get_lecture_attendance(cls, lecture_id):
        """Get attendance records for a lecture"""
        return cls.query.filter_by(lecture_id=lecture_id)\
                      .order_by(cls.timestamp.desc())\
                      .all()

    @classmethod
    def get_course_attendance(cls, course_id):
        """Get attendance records for a course"""
        return cls.query.join(Lecture)\
                      .filter(Lecture.course_id == course_id)\
                      .order_by(cls.timestamp.desc())\
                      .all()

    @classmethod
    def get_attendance_by_date(cls, date):
        """Get attendance records for a specific date"""
        return cls.query.filter(db.func.date(cls.timestamp) == date)\
                      .order_by(cls.timestamp.desc())\
                      .all()

    def update_status(self, status, marked_by_id=None, notes=None):
        """Update attendance status"""
        self.status = status
        if marked_by_id:
            self.marked_by_id = marked_by_id
        if notes:
            self.notes = notes
        db.session.commit()
