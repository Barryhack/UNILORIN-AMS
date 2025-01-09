from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    """User model for storing user details"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    id_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    fingerprint_data = db.Column(db.LargeBinary)
    rfid_data = db.Column(db.String(50))
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    department = db.relationship('Department', back_populates='users')
    courses = db.relationship('Course', back_populates='lecturer', foreign_keys='Course.lecturer_id')
    enrolled_courses = db.relationship(
        'Course',
        secondary='course_students',
        back_populates='enrolled_students',
        lazy=True
    )
    student_courses = db.relationship('CourseStudent', back_populates='student')
    attendances = db.relationship('Attendance', back_populates='student', foreign_keys='Attendance.student_id')
    marked_attendances = db.relationship('Attendance', back_populates='marked_by', foreign_keys='Attendance.marked_by_id')
    login_logs = db.relationship('LoginLog', back_populates='user')
    activity_logs = db.relationship('ActivityLog', back_populates='user')
    notifications = db.relationship('Notification', back_populates='user')
    
    def __init__(self, email, name, role, password=None, department_id=None, id_number=None):
        self.email = email
        self.name = name
        self.role = role
        self.department_id = department_id
        self.id_number = id_number
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        if not password:
            raise ValueError("Password cannot be empty")
        self.password_hash = generate_password_hash(password)
        logger.info(f"Password set for user {self.email}")
    
    def check_password(self, password):
        if not password:
            return False
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
        logger.info(f"Last login updated for user {self.email}")

    def get_dashboard_route(self):
        """Return the appropriate dashboard route based on user role."""
        if self.role == 'admin':
            return 'admin.dashboard'
        elif self.role == 'lecturer':
            return 'lecturer.dashboard'
        elif self.role == 'student':
            return 'student.dashboard'
        else:
            return 'main.index'  # Default route for unknown roles

    def __repr__(self):
        return f'<User {self.email}>'

# Create default admin, lecturer and student users if they don't exist.
def create_default_users():
    """Create default admin, lecturer and student users if they don't exist."""
    try:
        # Create admin user
        if not User.query.filter_by(id_number='ADMIN001').first():
            admin = User(
                email='admin@example.com',
                name='Admin User',
                role='admin',
                password='admin123',
                id_number='ADMIN001'
            )
            db.session.add(admin)
            logger.info("Created default admin user")

        # Create lecturer user
        if not User.query.filter_by(id_number='LECT001').first():
            lecturer = User(
                email='lecturer@example.com',
                name='Lecturer User',
                role='lecturer',
                password='lecturer123',
                id_number='LECT001'
            )
            db.session.add(lecturer)
            logger.info("Created default lecturer user")

        # Create student user
        if not User.query.filter_by(id_number='STU001').first():
            student = User(
                email='student@example.com',
                name='Student User',
                role='student',
                password='student123',
                id_number='STU001'
            )
            db.session.add(student)
            logger.info("Created default student user")

        db.session.commit()
        logger.info("Successfully created default users")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating default users: {str(e)}")
        raise
