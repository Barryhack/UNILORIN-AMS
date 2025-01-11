from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    """User model for storing user related details."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.String(20), nullable=False)  # admin, lecturer, student
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    fingerprint_data = db.Column(db.LargeBinary, nullable=True)

    # Relationships
    department = db.relationship('Department', backref='users')
    student_courses = db.relationship('Course', secondary='course_students',
                                    backref=db.backref('students', lazy='dynamic'),
                                    overlaps="enrolled_courses")
    enrolled_courses = db.relationship('Course', secondary='course_students',
                                     backref=db.backref('enrolled_students', lazy='dynamic'),
                                     overlaps="student_courses")
    attendances = db.relationship('Attendance', backref='user', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')
    login_logs = db.relationship('LoginLog', backref='user', lazy='dynamic')

    def __init__(self, login_id, email=None, first_name=None, last_name=None, role='student'):
        self.login_id = login_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = role

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_lecturer(self):
        return self.role == 'lecturer'

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.login_id

    def __repr__(self):
        return f'<User {self.login_id}>'

# Create default admin, lecturer and student users if they don't exist.
def create_default_users():
    """Create default admin, lecturer and student users if they don't exist."""
    try:
        # Create admin user
        if not User.query.filter_by(login_id='ADMIN001').first():
            admin = User(
                login_id='ADMIN001',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                role='admin',
                password='admin123'
            )
            db.session.add(admin)
            logger.info("Created default admin user")

        # Create lecturer user
        if not User.query.filter_by(login_id='LECT001').first():
            lecturer = User(
                login_id='LECT001',
                email='lecturer@example.com',
                first_name='Lecturer',
                last_name='User',
                role='lecturer',
                password='lecturer123'
            )
            db.session.add(lecturer)
            logger.info("Created default lecturer user")

        # Create student user
        if not User.query.filter_by(login_id='STU001').first():
            student = User(
                login_id='STU001',
                email='student@example.com',
                first_name='Student',
                last_name='User',
                role='student',
                password='student123'
            )
            db.session.add(student)
            logger.info("Created default student user")

        db.session.commit()
        logger.info("Successfully created default users")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating default users: {str(e)}")
        raise
