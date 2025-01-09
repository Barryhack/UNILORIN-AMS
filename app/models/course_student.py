"""Course-Student association model."""
from app.extensions import db
from datetime import datetime

class CourseStudent(db.Model):
    """Association model for courses and students (users with role='student')"""
    __tablename__ = 'course_students'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, dropped, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = db.relationship('Course', back_populates='course_students')
    student = db.relationship('User', back_populates='student_courses')

    def __repr__(self):
        return f'<CourseStudent {self.student.name} - {self.course.code}>'

    def to_dict(self):
        """Convert course student record to dictionary"""
        return {
            'id': self.id,
            'course_id': self.course_id,
            'student_id': self.student_id,
            'enrollment_date': self.enrollment_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'course': {
                'id': self.course.id,
                'code': self.course.code,
                'title': self.course.title
            } if self.course else None,
            'student': {
                'id': self.student.id,
                'name': self.student.name,
                'email': self.student.email
            } if self.student else None
        }
