from app import db
from datetime import datetime

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    units = db.Column(db.Integer, nullable=False, default=3)
    level = db.Column(db.Integer, nullable=False)  # e.g., 100, 200, 300, 400
    semester = db.Column(db.Integer, nullable=False)  # 1 or 2
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = db.relationship('Department', back_populates='courses')
    lectures = db.relationship('Lecture', back_populates='course_ref', lazy='dynamic')
    attendances = db.relationship('Attendance', back_populates='course', lazy='dynamic')
    students = db.relationship('Student', secondary='student_courses', back_populates='courses', lazy='dynamic')

    def __init__(self, code, title, description=None, units=3, level=100, semester=1, department_id=None):
        self.code = code
        self.title = title
        self.description = description
        self.units = units
        self.level = level
        self.semester = semester
        self.department_id = department_id

    def __repr__(self):
        return f'<Course {self.code}>'

    @property
    def total_students(self):
        """Get the total number of students enrolled in this course"""
        return len(self.students) if self.students else 0

    @property
    def total_lectures(self):
        """Get the total number of lectures for this course"""
        return self.lectures.count()

    @property
    def average_attendance(self):
        """Calculate the average attendance rate for this course"""
        total_lectures = self.total_lectures
        if total_lectures == 0:
            return 0
        
        total_attendance = sum(lecture.attendance_count for lecture in self.lectures)
        return (total_attendance / (total_lectures * self.total_students)) * 100 if self.total_students > 0 else 0
