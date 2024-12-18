from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import String

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(String(50), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # admin, lecturer, student
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = db.relationship('Department', back_populates='users')
    student = db.relationship('Student', back_populates='user', uselist=False)
    lectures = db.relationship('Lecture', back_populates='lecturer_ref', lazy='dynamic')

    def __init__(self, id, email, name, role, department_id=None):
        self.id = id
        self.email = email
        self.name = name
        self.role = role
        self.department_id = department_id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_lecturer(self):
        return self.role == 'lecturer'

    @property
    def is_student(self):
        return self.role == 'student'

    def get_dashboard_route(self):
        """Return the appropriate dashboard route based on user role"""
        if self.is_admin:
            return 'admin.dashboard'
        elif self.is_lecturer:
            return 'lecturer.dashboard'
        elif self.is_student:
            return 'student.dashboard'
        return 'main.index'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    @classmethod
    def find_by_login(cls, login):
        """Find a user by their email (login)"""
        return cls.query.filter_by(email=login).first()

    @classmethod
    def find_by_id(cls, id):
        """Find a user by their ID"""
        return cls.query.get(id)
