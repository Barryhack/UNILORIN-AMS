from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship


class Student(db.Model):
    """Model for students"""
    __tablename__ = 'students'

    id = db.Column(db.String(10), primary_key=True)  # For IDs like 'ST001'
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50), nullable=False)  # e.g., '100L', '200L', etc.
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    attendances = relationship('Attendance', back_populates='student')

    def __repr__(self):
        return f'<Student {self.name}>'

    def to_dict(self):
        """Convert student object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'student_id': self.student_id,
            'department': self.department,
            'level': self.level,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def attendance_rate(self):
        """Calculate student's overall attendance rate"""
        total_attendances = len(self.attendances)
        if total_attendances == 0:
            return 0
        present_count = sum(1 for a in self.attendances if a.status == 'present')
        return (present_count / total_attendances) * 100

    def course_attendance_rate(self, course_id):
        """Calculate student's attendance rate for a specific course"""
        course_attendances = [a for a in self.attendances if a.lecture.course_id == course_id]
        total_attendances = len(course_attendances)
        if total_attendances == 0:
            return 0
        present_count = sum(1 for a in course_attendances if a.status == 'present')
        return (present_count / total_attendances) * 100

    def get_attendance_history(self, course_id=None):
        """Get student's attendance history, optionally filtered by course"""
        query = self.attendances
        if course_id:
            query = [a for a in query if a.lecture.course_id == course_id]
        return sorted(query, key=lambda x: x.lecture.date, reverse=True)

    def get_enrolled_courses(self):
        """Get list of courses student is enrolled in"""
        return self.courses

    def enroll_in_course(self, course):
        """Enroll student in a course"""
        if course not in self.courses:
            self.courses.append(course)
            db.session.commit()

    def unenroll_from_course(self, course):
        """Remove student from a course"""
        if course in self.courses:
            self.courses.remove(course)
            db.session.commit()

    @classmethod
    def get_by_student_id(cls, student_id):
        """Get student by their student ID"""
        return cls.query.filter_by(student_id=student_id).first()

    @classmethod
    def get_by_email(cls, email):
        """Get student by their email"""
        return cls.query.filter_by(email=email).first()

    @classmethod
    def get_by_department(cls, department):
        """Get all students in a department"""
        return cls.query.filter_by(department=department).all()

    @classmethod
    def get_by_level(cls, level):
        """Get all students in a specific level"""
        return cls.query.filter_by(level=level).all()
