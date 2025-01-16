"""Course lecturer model."""
from datetime import datetime
from app.extensions import db

class CourseLecturer(db.Model):
    """Course lecturer model."""

    __tablename__ = 'course_lecturers'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = db.relationship('Course', backref=db.backref('course_lecturers', lazy=True))
    lecturer = db.relationship('User', backref=db.backref('course_lecturers', lazy=True))

    def __repr__(self):
        """Return string representation."""
        return f'<CourseLecturer {self.course.code} - {self.lecturer.email}>'
