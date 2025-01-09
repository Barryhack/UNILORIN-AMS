from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

class BaseForm(FlaskForm):
    """Base form class that ensures CSRF protection is enabled"""
    class Meta:
        csrf = True  # Enable CSRF protection by default
        csrf_time_limit = 3600  # 1 hour

from .auth_forms import LoginForm
from .settings import SystemSettingsForm

# Update all forms to inherit from BaseForm
LoginForm.__bases__ = (BaseForm,)
SystemSettingsForm.__bases__ = (BaseForm,)
