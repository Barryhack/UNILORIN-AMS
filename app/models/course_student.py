"""Course-Student association model."""
from datetime import datetime
from app.extensions import db

class CourseStudent(db.Model):
    """Association model for Course-Student relationship."""
    __tablename__ = 'course_students'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

    # Relationships with proper overlaps configuration
    course = db.relationship(
        'Course',
        back_populates='course_students',
        overlaps="enrolled_students,enrolled_courses"
    )
    student = db.relationship(
        'User',
        back_populates='course_enrollments',
        overlaps="enrolled_courses,enrolled_students"
    )

    def __init__(self, course_id, student_id, status='active'):
        """Initialize a new course-student relationship."""
        self.course_id = course_id
        self.student_id = student_id
        self.status = status

    def __repr__(self):
        """String representation of the course-student relationship."""
        return f'<CourseStudent {self.course_id}-{self.student_id}>'
