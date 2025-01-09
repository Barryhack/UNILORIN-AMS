from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from datetime import timedelta

class Attendance(db.Model):
    """Attendance model for tracking student attendance in lectures"""
    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    student_id = db.Column(db.String(10), db.ForeignKey('students.id'), nullable=False)
    status = db.Column(db.String(20), default='present')  # present, absent, late, excused
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    marked_by_id = db.Column(db.String(10), db.ForeignKey('users.id'))  # if marked by lecturer/admin
    latitude = db.Column(db.Float)  # for location-based attendance
    longitude = db.Column(db.Float)
    device_info = db.Column(db.String(200))  # device used to mark attendance
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lecture = relationship('Lecture', back_populates='attendances')
    student = relationship('Student', back_populates='attendances')
    marked_by = relationship('User', back_populates='marked_attendances')

    def __repr__(self):
        return f'<Attendance {self.student.name} - {self.lecture.date} - {self.status}>'

    def to_dict(self):
        """Convert attendance object to dictionary"""
        return {
            'id': self.id,
            'lecture_id': self.lecture_id,
            'student_id': self.student_id,
            'status': self.status,
            'marked_at': self.marked_at.isoformat() if self.marked_at else None,
            'marked_by_id': self.marked_by_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'device_info': self.device_info,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'student_name': self.student.name if self.student else None,
            'lecture_date': self.lecture.date.isoformat() if self.lecture else None,
            'course_code': self.lecture.course.code if self.lecture and self.lecture.course else None
        }

    def mark_present(self, marked_by=None, latitude=None, longitude=None, device_info=None, notes=None):
        """Mark student as present"""
        self.status = 'present'
        self._update_attendance_details(marked_by, latitude, longitude, device_info, notes)

    def mark_absent(self, marked_by=None, notes=None):
        """Mark student as absent"""
        self.status = 'absent'
        self._update_attendance_details(marked_by, notes=notes)

    def mark_late(self, marked_by=None, latitude=None, longitude=None, device_info=None, notes=None):
        """Mark student as late"""
        self.status = 'late'
        self._update_attendance_details(marked_by, latitude, longitude, device_info, notes)

    def mark_excused(self, marked_by=None, notes=None):
        """Mark student as excused"""
        self.status = 'excused'
        self._update_attendance_details(marked_by, notes=notes)

    def _update_attendance_details(self, marked_by=None, latitude=None, longitude=None, device_info=None, notes=None):
        """Update attendance details"""
        self.marked_at = datetime.utcnow()
        if marked_by:
            self.marked_by_id = marked_by.id
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude
        if device_info:
            self.device_info = device_info
        if notes:
            self.notes = notes
        db.session.commit()

    def is_within_valid_time(self, grace_period_minutes=15):
        """Check if attendance was marked within valid time"""
        if not self.marked_at or not self.lecture:
            return False
        
        lecture_start = datetime.combine(self.lecture.date, self.lecture.start_time)
        lecture_end = datetime.combine(self.lecture.date, self.lecture.end_time)
        grace_end = lecture_end + timedelta(minutes=grace_period_minutes)
        
        return lecture_start <= self.marked_at <= grace_end

    def is_within_valid_location(self, class_latitude, class_longitude, radius_meters=100):
        """Check if attendance was marked within valid location radius"""
        if self.latitude is None or self.longitude is None:
            return False
        
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth's radius in meters
        lat1, lon1 = radians(class_latitude), radians(class_longitude)
        lat2, lon2 = radians(self.latitude), radians(self.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance <= radius_meters

    @classmethod
    def get_by_lecture(cls, lecture_id):
        """Get all attendance records for a lecture"""
        return cls.query.filter_by(lecture_id=lecture_id).all()

    @classmethod
    def get_by_student(cls, student_id):
        """Get all attendance records for a student"""
        return cls.query.filter_by(student_id=student_id).all()

    @classmethod
    def get_by_date_range(cls, start_date, end_date):
        """Get attendance records within a date range"""
        return cls.query.join(Lecture).filter(
            Lecture.date >= start_date,
            Lecture.date <= end_date
        ).all()

    @classmethod
    def get_by_course(cls, course_id):
        """Get all attendance records for a course"""
        return cls.query.join(Lecture).filter(Lecture.course_id == course_id).all()

    @classmethod
    def get_student_attendance_rate(cls, student_id, course_id=None):
        """Calculate attendance rate for a student"""
        query = cls.query.filter_by(student_id=student_id)
        if course_id:
            query = query.join(Lecture).filter(Lecture.course_id == course_id)
        
        total = query.count()
        if total == 0:
            return 0
        
        present = query.filter(cls.status.in_(['present', 'late'])).count()
        return (present / total * 100)
