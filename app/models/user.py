"""User model for storing user related details."""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
import logging
from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    """User model for storing user related details."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login_id = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(128))
    first_name = Column(String(64))
    last_name = Column(String(64))
    role = Column(String(20), nullable=False)  # admin, lecturer, student
    department_id = Column(Integer, ForeignKey('departments.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    fingerprint_data = Column(LargeBinary, nullable=True)

    # Relationships with proper overlaps configuration
    department = relationship('Department', back_populates='department_users')
    enrolled_courses = relationship(
        'Course', 
        secondary='course_students',
        back_populates='enrolled_students',
        lazy='dynamic',
        overlaps="course_enrollments,course_students"
    )
    course_enrollments = relationship(
        'CourseStudent',
        back_populates='student',
        overlaps="enrolled_courses,enrolled_students"
    )
    taught_courses = relationship(
        'Course',
        foreign_keys='Course.lecturer_id',
        back_populates='lecturer',
        lazy='dynamic'
    )
    attendances = relationship(
        'Attendance',
        foreign_keys='Attendance.user_id',
        back_populates='user',
        lazy='dynamic'
    )
    marked_attendances = relationship(
        'Attendance',
        foreign_keys='Attendance.marked_by_id',
        back_populates='marked_by',
        lazy='dynamic'
    )
    activity_logs = relationship(
        'ActivityLog',
        back_populates='user',
        lazy='dynamic'
    )
    login_logs = relationship(
        'LoginLog',
        back_populates='user',
        lazy='dynamic'
    )
    notifications = relationship(
        'Notification',
        back_populates='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __init__(self, login_id, email=None, first_name=None, last_name=None, role='student'):
        """Initialize a new user."""
        self.login_id = login_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = role

    @property
    def name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def password(self):
        """Prevent password from being accessed."""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """Set password to a hashed password."""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Check if hashed password matches actual password."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'login_id': self.login_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'department_id': self.department_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    @classmethod
    def create_default_users(cls):
        """Create default admin, lecturer and student users if they don't exist."""
        try:
            # Create admin user if not exists
            if not cls.query.filter_by(login_id='ADMIN001').first():
                admin = cls(
                    login_id='ADMIN001',
                    email='admin@example.com',
                    first_name='Admin',
                    last_name='User',
                    role='admin'
                )
                admin.password = 'admin123'
                db.session.add(admin)
                logger.info("Created default admin user")

            # Create lecturer user if not exists
            if not cls.query.filter_by(login_id='LECT001').first():
                lecturer = cls(
                    login_id='LECT001',
                    email='lecturer@example.com',
                    first_name='Lecturer',
                    last_name='User',
                    role='lecturer'
                )
                lecturer.password = 'lecturer123'
                db.session.add(lecturer)
                logger.info("Created default lecturer user")

            # Create student user if not exists
            if not cls.query.filter_by(login_id='STU001').first():
                student = cls(
                    login_id='STU001',
                    email='student@example.com',
                    first_name='Student',
                    last_name='User',
                    role='student'
                )
                student.password = 'student123'
                db.session.add(student)
                logger.info("Created default student user")

            db.session.commit()
            logger.info("All default users created successfully")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating default users: {str(e)}")
            raise

    def __repr__(self):
        """String representation of the User model."""
        return f'<User {self.login_id}>'
