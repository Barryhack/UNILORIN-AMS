from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship

class Faculty(db.Model):
    """Faculty model for managing faculty information"""
    __tablename__ = 'faculties'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    departments = relationship('Department', back_populates='faculty', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Faculty {self.name}>'

    def to_dict(self):
        """Convert faculty to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'department_count': len(self.departments) if self.departments else 0
        }

    @classmethod
    def get_by_id(cls, faculty_id):
        """Get faculty by ID"""
        return cls.query.get(faculty_id)

    @classmethod
    def get_by_code(cls, code):
        """Get faculty by code"""
        return cls.query.filter_by(code=code).first()

    @classmethod
    def get_all_active(cls):
        """Get all active faculties"""
        return cls.query.filter_by(is_active=True).all()

    def add_department(self, department):
        """Add a department to this faculty"""
        if department not in self.departments:
            self.departments.append(department)
            db.session.commit()

    def remove_department(self, department):
        """Remove a department from this faculty"""
        if department in self.departments:
            self.departments.remove(department)
            db.session.commit()

    def update_info(self, name=None, code=None, description=None, is_active=None):
        """Update faculty information"""
        if name is not None:
            self.name = name
        if code is not None:
            self.code = code
        if description is not None:
            self.description = description
        if is_active is not None:
            self.is_active = is_active
        
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def get_department_count(self):
        """Get the number of departments in this faculty"""
        return len(self.departments)

    def get_active_departments(self):
        """Get all active departments in this faculty"""
        return [dept for dept in self.departments if dept.is_active]

    def get_courses(self):
        """Get all courses associated with this faculty's departments"""
        courses = []
        for department in self.departments:
            courses.extend(department.courses)
        return courses

    def get_students_count(self):
        """Get total number of students in all departments"""
        count = 0
        for department in self.departments:
            count += department.get_students_count()
        return count

    def get_lecturers_count(self):
        """Get total number of lecturers in all departments"""
        count = 0
        for department in self.departments:
            count += department.get_lecturers_count()
        return count

def create_default_faculties():
    """Create default faculties if they don't exist"""
    print("Creating default faculties...")
    
    try:
        # Check if default faculty already exists
        if Faculty.query.filter_by(code='SICT').first():
            print("Default faculties already exist")
            return

        # Create default faculty
        faculty = Faculty(
            name='School of Information and Communication Technology',
            code='SICT'
        )
        db.session.add(faculty)
        db.session.commit()
        print("Successfully created default faculties")
        
        return faculty
    except Exception as e:
        print(f"Error creating default faculties: {str(e)}")
        db.session.rollback()
        raise
