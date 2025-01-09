from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, ValidationError, Length, EqualTo
from app.models.user import User
from flask import session

class LoginForm(FlaskForm):
    """Form for user login"""
    login = StringField('ID Number', validators=[
        DataRequired(message='Please enter your ID number'),
        Length(max=20, message='ID number must be less than 20 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password')
    ])
    remember = BooleanField('Remember Me')
    csrf_token = HiddenField()
    submit = SubmitField('Log In')

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        if not self.csrf_token.data:
            self.csrf_token.data = session.get('csrf_token')

class ChangePasswordForm(FlaskForm):
    """Form for changing password"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')
