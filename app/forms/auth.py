from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Length, EqualTo
from app.models.user import User
from app.forms import BaseForm

class LoginForm(BaseForm):
    """Form for user login"""
    login = StringField('ID Number', validators=[
        DataRequired(message='Please enter your ID number'),
        Length(max=20, message='ID number must be less than 20 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password')
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

    class Meta:
        csrf = True

class ChangePasswordForm(BaseForm):
    """Form for changing password"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')
