from app import db
from app.models.user import User
from app.models.course import Course

# Association table for student-course relationship
student_courses = db.Table('student_courses',
    db.Column('student_id', db.String(50), db.ForeignKey('students.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
)

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False, unique=True)
    matric_number = db.Column(db.String(20), unique=True, nullable=False)
    level = db.Column(db.Integer, nullable=False)  # e.g., 100, 200, 300, 400
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='student')
    department = db.relationship('Department', back_populates='students')
    courses = db.relationship('Course', secondary=student_courses, back_populates='students')
    attendances = db.relationship('Attendance', back_populates='student', lazy='dynamic')

    def __init__(self, user_id, matric_number, level, department_id):
        self.id = user_id  # Using the same ID as the user
        self.user_id = user_id
        self.matric_number = matric_number
        self.level = level
        self.department_id = department_id

    @property
    def name(self):
        """Get the student's full name from the associated user"""
        if self.user:
            return self.user.name
        return "Unknown"

    @property
    def email(self):
        """Get the student's email from the associated user"""
        if self.user:
            return self.user.email
        return None

    def __repr__(self):
        return f'<Student {self.matric_number}>'
