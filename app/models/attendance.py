from app import db
from datetime import datetime

class Attendance(db.Model):
    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.id'), nullable=False)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='present')  # present, absent, late
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='attendances')
    course = db.relationship('Course', back_populates='attendances')
    lecture = db.relationship('Lecture', back_populates='attendances')

    def __init__(self, student_id, lecture_id, course_id, status='present'):
        self.student_id = student_id
        self.lecture_id = lecture_id
        self.course_id = course_id
        self.status = status
        self.timestamp = datetime.utcnow()

    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.lecture_id}>'
