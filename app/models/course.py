from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship

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
    lecturer = db.relationship('User', foreign_keys=[lecturer_id], backref=db.backref('taught_courses', lazy='dynamic'))
    course_students = db.relationship('CourseStudent', back_populates='course')
    enrolled_students = db.relationship(
        'User',
        secondary='course_students',
        back_populates='enrolled_courses',
        lazy=True
    )
    lectures = relationship('Lecture', back_populates='course', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', back_populates='course', lazy='dynamic')

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
            'department': self.department.name if self.department else None,
            'lecturer': self.lecturer.name if self.lecturer else None,
            'student_count': len(self.enrolled_students)
        }

    def get_enrolled_students(self):
        """Get all students enrolled in the course"""
        return self.enrolled_students

    def get_student_count(self):
        """Get number of enrolled students"""
        return len(self.enrolled_students)

    def get_attendance_rate(self):
        """Calculate overall attendance rate for the course"""
        total_attendance = 0
        total_possible = 0
        for lecture in self.lectures:
            present_count = sum(1 for a in lecture.attendances if a.status == 'present')
            total_attendance += present_count
            total_possible += len(lecture.attendances)
        return (total_attendance / total_possible * 100) if total_possible > 0 else 0

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

    def enroll_student(self, student):
        """Enroll a student in the course"""
        if student not in self.enrolled_students:
            self.enrolled_students.append(student)
            db.session.commit()

    def unenroll_student(self, student):
        """Remove a student from the course"""
        if student in self.enrolled_students:
            self.enrolled_students.remove(student)
            db.session.commit()

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
