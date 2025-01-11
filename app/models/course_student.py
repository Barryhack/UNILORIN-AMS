"""Course-Student association model."""
from app.extensions import db
from datetime import datetime

class CourseStudent(db.Model):
    """Association model for Course-Student relationship."""
    __tablename__ = 'course_students'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, dropped, completed

    # Relationships
    course = db.relationship('Course', back_populates='course_students')
    student = db.relationship('User', back_populates='course_enrollments')

    def __init__(self, course_id, student_id, status='active'):
        self.course_id = course_id
        self.student_id = student_id
        self.status = status

    def __repr__(self):
        return f'<CourseStudent {self.course_id}:{self.student_id}>'
