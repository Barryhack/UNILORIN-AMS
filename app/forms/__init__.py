"""Forms package."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

class BaseForm(FlaskForm):
    """Base form class that ensures CSRF protection is enabled"""
    class Meta:
        csrf = True  # Enable CSRF protection by default
        csrf_time_limit = 3600  # 1 hour

# Import all forms
from .user import UserForm
from .course import CourseForm
from .department import DepartmentForm
from .attendance import AttendanceForm
from .settings import SettingsForm
from .auth import LoginForm, ChangePasswordForm

# List all forms for easy access
__all__ = [
    'BaseForm',
    'UserForm',
    'CourseForm',
    'DepartmentForm',
    'AttendanceForm',
    'SettingsForm',
    'LoginForm',
    'ChangePasswordForm'
]
