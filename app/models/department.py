from app.extensions import db
from app.models.faculty import Faculty
from datetime import datetime
from sqlalchemy.orm import relationship

class Department(db.Model):
    """Department model for managing academic departments"""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculties.id'), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    faculty = relationship('Faculty', back_populates='departments')
    users = relationship('User', back_populates='department')
    courses = relationship('Course', back_populates='department')

    def __repr__(self):
        return f'<Department {self.name}>'

    def to_dict(self):
        """Convert department object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'faculty_id': self.faculty_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'faculty': self.faculty.name if self.faculty else None
        }

    def get_active_courses(self):
        """Get all active courses in the department"""
        return [course for course in self.courses if course.is_active]

    def get_lecturers(self):
        """Get all lecturers in the department"""
        return [user for user in self.users if user.role == 'lecturer']

    def get_students(self):
        """Get all students in the department"""
        return [user for user in self.users if user.role == 'student']

    def get_course_count(self):
        """Get total number of courses in the department"""
        return len(self.courses)

    def get_user_count(self, role=None):
        """Get total number of users in the department, optionally filtered by role"""
        if role:
            return len([user for user in self.users if user.role == role])
        return len(self.users)

    @classmethod
    def get_by_code(cls, code):
        """Get department by code"""
        return cls.query.filter_by(code=code).first()

    @classmethod
    def get_active_departments(cls):
        """Get all active departments"""
        return cls.query.filter_by(is_active=True).all()

    @classmethod
    def get_by_faculty(cls, faculty_id):
        """Get all departments in a faculty"""
        return cls.query.filter_by(faculty_id=faculty_id).all()

    def update(self, **kwargs):
        """Update department attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def delete(self):
        """Soft delete the department"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def restore(self):
        """Restore a soft-deleted department"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()

def create_default_departments():
    """Create default departments if they don't exist"""
    print("Creating default departments...")
    
    try:
        # Check if default department already exists
        if Department.query.filter_by(code='CSC').first():
            print("Default departments already exist")
            return

        # Get the SICT faculty
        faculty = Faculty.query.filter_by(code='SICT').first()
        if not faculty:
            print("SICT faculty not found")
            return

        # Create default departments
        departments = [
            Department(
                name='Computer Science',
                code='CSC',
                faculty_id=faculty.id
            ),
            Department(
                name='Information Technology',
                code='IT',
                faculty_id=faculty.id
            ),
            Department(
                name='Library and Information Science',
                code='LIS',
                faculty_id=faculty.id
            )
        ]
        
        db.session.add_all(departments)
        db.session.commit()
        print("Successfully created default departments")
        
        return departments
    except Exception as e:
        print(f"Error creating default departments: {str(e)}")
        db.session.rollback()
        raise
