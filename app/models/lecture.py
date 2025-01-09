from app.extensions import db
from datetime import datetime, time
from sqlalchemy.orm import relationship

class Lecture(db.Model):
    """Lecture model for managing course lectures"""
    __tablename__ = 'lectures'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(50))
    topic = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, ongoing, completed, cancelled
    notes = db.Column(db.Text)

    # Relationships
    course = relationship('Course', back_populates='lectures')
    attendances = relationship('Attendance', back_populates='lecture', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Lecture {self.course.code} on {self.date} at {self.start_time}>'

    def to_dict(self):
        """Convert lecture object to dictionary"""
        return {
            'id': self.id,
            'course_id': self.course_id,
            'date': self.date.isoformat() if self.date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'room': self.room,
            'topic': self.topic,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'status': self.status,
            'notes': self.notes,
            'course': self.course.code if self.course else None,
            'attendance_count': len(self.attendances),
            'attendance_rate': self.get_attendance_rate()
        }

    def get_attendance_rate(self):
        """Calculate attendance rate for this lecture"""
        total_students = len(self.course.students)
        if total_students == 0:
            return 0
        present_count = sum(1 for a in self.attendances if a.status == 'present')
        return (present_count / total_students * 100)

    def get_present_students(self):
        """Get list of students present in the lecture"""
        return [a.student for a in self.attendances if a.status == 'present']

    def get_absent_students(self):
        """Get list of students absent from the lecture"""
        present_student_ids = {a.student_id for a in self.attendances if a.status == 'present'}
        return [s for s in self.course.students if s.id not in present_student_ids]

    def mark_attendance(self, student, status='present', latitude=None, longitude=None):
        """Mark attendance for a student"""
        from app.models.attendance import Attendance
        attendance = next((a for a in self.attendances if a.student_id == student.id), None)
        if attendance:
            attendance.status = status
            attendance.latitude = latitude
            attendance.longitude = longitude
            attendance.marked_at = datetime.utcnow()
        else:
            attendance = Attendance(
                lecture_id=self.id,
                student_id=student.id,
                status=status,
                latitude=latitude,
                longitude=longitude
            )
            self.attendances.append(attendance)
        db.session.commit()

    def start_lecture(self):
        """Start the lecture"""
        if self.status == 'scheduled':
            self.status = 'ongoing'
            db.session.commit()

    def end_lecture(self):
        """End the lecture"""
        if self.status == 'ongoing':
            self.status = 'completed'
            db.session.commit()

    def cancel_lecture(self, reason=None):
        """Cancel the lecture"""
        self.status = 'cancelled'
        if reason:
            self.notes = reason
        db.session.commit()

    def reschedule(self, new_date, new_start_time, new_end_time):
        """Reschedule the lecture"""
        self.date = new_date
        self.start_time = new_start_time
        self.end_time = new_end_time
        self.status = 'scheduled'
        db.session.commit()

    def is_ongoing(self):
        """Check if lecture is currently ongoing"""
        now = datetime.utcnow()
        return (self.date == now.date() and 
                self.start_time <= now.time() <= self.end_time and 
                self.status == 'ongoing')

    def can_mark_attendance(self):
        """Check if attendance can be marked"""
        now = datetime.utcnow()
        buffer_time = time(minutes=15)  # 15 minutes buffer after end time
        return (self.date == now.date() and 
                self.start_time <= now.time() <= (self.end_time + buffer_time) and 
                self.status in ['scheduled', 'ongoing'])

    def update(self, **kwargs):
        """Update lecture attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def delete(self):
        """Soft delete the lecture"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def restore(self):
        """Restore a soft-deleted lecture"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def get_by_date(cls, date):
        """Get all lectures on a specific date"""
        return cls.query.filter_by(date=date).all()

    @classmethod
    def get_by_course(cls, course_id):
        """Get all lectures for a specific course"""
        return cls.query.filter_by(course_id=course_id).all()

    @classmethod
    def get_active_lectures(cls):
        """Get all active lectures"""
        return cls.query.filter_by(is_active=True).all()

    @classmethod
    def get_ongoing_lectures(cls):
        """Get currently ongoing lectures"""
        now = datetime.utcnow()
        return cls.query.filter(
            cls.date == now.date(),
            cls.start_time <= now.time(),
            cls.end_time >= now.time(),
            cls.status == 'ongoing'
        ).all()

    @classmethod
    def get_upcoming_lectures(cls):
        """Get upcoming lectures"""
        now = datetime.utcnow()
        return cls.query.filter(
            (cls.date > now.date()) |
            ((cls.date == now.date()) & (cls.start_time > now.time())),
            cls.status == 'scheduled'
        ).all()
