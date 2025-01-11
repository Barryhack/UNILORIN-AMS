from flask import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    """Form for user login."""
    login = StringField('Login ID', validators=[
        DataRequired(),
        Length(min=3, max=20, message='Login ID must be between 3 and 20 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ChangePasswordForm(FlaskForm):
    """Form for changing password"""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Please enter your current password')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='Please enter a new password'),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        validators.EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')

    def validate_current_password(self, field):
        """Validate that the current password is correct."""
        if not current_user.check_password(field.data):
            raise ValidationError('Current password is incorrect')
