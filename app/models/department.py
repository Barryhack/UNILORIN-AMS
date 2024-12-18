from app import db
from datetime import datetime

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    courses = db.relationship('Course', back_populates='department', lazy='dynamic')
    students = db.relationship('Student', back_populates='department', lazy='dynamic')
    users = db.relationship('User', back_populates='department', lazy='dynamic')

    def __init__(self, name, code):
        self.name = name
        self.code = code

    def __repr__(self):
        return f'<Department {self.code}>'

    @property
    def total_students(self):
        """Get the total number of students in this department"""
        return self.students.count()

    @property
    def total_courses(self):
        """Get the total number of courses in this department"""
        return self.courses.count()

    @property
    def total_lecturers(self):
        """Get the total number of lecturers in this department"""
        return self.users.filter_by(role='lecturer').count()
