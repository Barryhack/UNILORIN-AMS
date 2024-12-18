from app import db
from datetime import datetime

class Lecture(db.Model):
    __tablename__ = 'lectures'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lecturer_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    topic = db.Column(db.String(200))
    day_of_week = db.Column(db.String(10), nullable=False)  # Monday, Tuesday, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course_ref = db.relationship('Course', back_populates='lectures')
    lecturer_ref = db.relationship('User', back_populates='lectures')
    attendances = db.relationship('Attendance', back_populates='lecture', lazy='dynamic')

    def __init__(self, course_id, lecturer_id, date, start_time, end_time, topic=None):
        self.course_id = course_id
        self.lecturer_id = lecturer_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.topic = topic
        self.day_of_week = date.strftime('%A')  # Automatically set day_of_week based on date

    def __repr__(self):
        return f'<Lecture {self.course_id} - {self.date}>'

    @property
    def attendance_count(self):
        """Get the total number of students who attended this lecture"""
        return self.attendances.count()

    @property
    def attendance_rate(self):
        """Calculate the attendance rate for this lecture"""
        total_students = self.course_ref.total_students
        if total_students == 0:
            return 0
        return (self.attendance_count / total_students) * 100
