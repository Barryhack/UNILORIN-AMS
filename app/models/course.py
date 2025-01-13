from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from .lecture import Lecture

class Course(db.Model):
    """Course model for managing academic courses"""
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer, default=3)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    semester = db.Column(db.String(20))  # e.g., 'Fall 2023'
    level = db.Column(db.String(10))  # e.g., '100L', '200L'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    department = db.relationship('Department', back_populates='courses')
    lecturer = db.relationship('User', foreign_keys=[lecturer_id], back_populates='taught_courses')
    enrolled_students = db.relationship(
        'User',
        secondary='course_students',
        back_populates='enrolled_courses',
        lazy='dynamic',
        overlaps="course_students,course_enrollments"
    )
    course_students = db.relationship(
        'CourseStudent',
        back_populates='course',
        overlaps="enrolled_students,enrolled_courses"
    )
    lectures = db.relationship('Lecture', 
                             back_populates='course', 
                             cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.code}: {self.title}>'

    def to_dict(self):
        """Convert course object to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'credits': self.credits,
            'department_id': self.department_id,
            'lecturer_id': self.lecturer_id,
            'semester': self.semester,
            'level': self.level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'department': self.department.to_dict() if self.department else None,
            'lecturer': {
                'id': self.lecturer.id,
                'name': self.lecturer.name,
                'email': self.lecturer.email
            } if self.lecturer else None,
            'enrolled_students_count': self.enrolled_students.count() if hasattr(self.enrolled_students, 'count') else len(self.enrolled_students)
        }

    def add_student(self, student, status='enrolled'):
        """Add a student to the course"""
        if not self.is_student_enrolled(student):
            enrollment = CourseStudent(course=self, student=student, status=status)
            db.session.add(enrollment)
            try:
                db.session.commit()
                return True
            except Exception as e:
                db.session.rollback()
                return False
        return False

    def remove_student(self, student):
        """Remove a student from the course"""
        enrollment = CourseStudent.query.filter_by(
            course_id=self.id,
            student_id=student.id
        ).first()
        if enrollment:
            db.session.delete(enrollment)
            try:
                db.session.commit()
                return True
            except Exception as e:
                db.session.rollback()
                return False
        return False

    def is_student_enrolled(self, student):
        """Check if a student is enrolled in the course"""
        return CourseStudent.query.filter_by(
            course_id=self.id,
            student_id=student.id
        ).first() is not None

    def get_attendance_stats(self):
        """Get attendance statistics for the course"""
        total_lectures = self.lectures.count()
        if total_lectures == 0:
            return {
                'total_lectures': 0,
                'total_students': 0,
                'average_attendance': 0,
                'attendance_by_lecture': []
            }

        total_students = self.enrolled_students.count()
        attendance_by_lecture = []

        for lecture in self.lectures:
            attended = lecture.attendances.filter_by(status='present').count()
            attendance_by_lecture.append({
                'lecture_id': lecture.id,
                'title': lecture.title,
                'date': lecture.date.strftime('%Y-%m-%d'),
                'attendance_count': attended,
                'attendance_percentage': (attended / total_students * 100) if total_students > 0 else 0
            })

        total_attendance = sum(item['attendance_count'] for item in attendance_by_lecture)
        average_attendance = (total_attendance / (total_lectures * total_students) * 100) if total_students > 0 else 0

        return {
            'total_lectures': total_lectures,
            'total_students': total_students,
            'average_attendance': average_attendance,
            'attendance_by_lecture': attendance_by_lecture
        }

    def get_enrolled_students(self):
        """Get all students enrolled in the course"""
        return self.enrolled_students

    def get_student_count(self):
        """Get number of enrolled students"""
        return len(self.enrolled_students)

    def get_lecture_count(self):
        """Get total number of lectures"""
        return len(self.lectures)

    def get_upcoming_lectures(self):
        """Get upcoming lectures"""
        now = datetime.utcnow()
        return [l for l in self.lectures if l.date > now.date() or 
                (l.date == now.date() and l.start_time > now.time())]

    def get_past_lectures(self):
        """Get past lectures"""
        now = datetime.utcnow()
        return [l for l in self.lectures if l.date < now.date() or 
                (l.date == now.date() and l.end_time < now.time())]

    def get_active_lecture(self):
        """Get currently active lecture if any"""
        now = datetime.utcnow()
        return next((l for l in self.lectures 
                    if l.date == now.date() 
                    and l.start_time <= now.time() <= l.end_time), None)

    def update(self, **kwargs):
        """Update course attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def delete(self):
        """Soft delete the course"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def restore(self):
        """Restore a soft-deleted course"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def get_by_code(cls, code):
        """Get course by code"""
        return cls.query.filter_by(code=code).first()

    @classmethod
    def get_active_courses(cls):
        """Get all active courses"""
        return cls.query.filter_by(is_active=True).all()

    @classmethod
    def get_by_department(cls, department_id):
        """Get all courses in a department"""
        return cls.query.filter_by(department_id=department_id).all()

    @classmethod
    def get_by_lecturer(cls, lecturer_id):
        """Get all courses taught by a lecturer"""
        return cls.query.filter_by(lecturer_id=lecturer_id).all()

    @classmethod
    def get_by_semester(cls, semester):
        """Get all courses in a semester"""
        return cls.query.filter_by(semester=semester).all()

    @classmethod
    def get_by_level(cls, level):
        """Get all courses for a specific level"""
        return cls.query.filter_by(level=level).all()

# Create default courses if they don't exist
def create_default_courses():
    """Create default courses if they don't exist."""
    try:
        # Get Computer Science department
        from .department import Department
        cs_dept = Department.query.filter_by(code='CSC').first()
        if not cs_dept:
            return

        # Create default courses
        if not Course.query.filter_by(code='CSC101').first():
            course = Course(
                code='CSC101',
                title='Introduction to Computer Science',
                department_id=cs_dept.id,
                description='Basic concepts of computer science'
            )
            db.session.add(course)

        if not Course.query.filter_by(code='CSC102').first():
            course = Course(
                code='CSC102',
                title='Programming Fundamentals',
                department_id=cs_dept.id,
                description='Introduction to programming concepts'
            )
            db.session.add(course)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default courses: {e}")
