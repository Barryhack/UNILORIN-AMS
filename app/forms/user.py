"""User forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from ..models import User, Department

class UserForm(FlaskForm):
    """Form for creating/editing users."""
    
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    
    role = SelectField('Role', validators=[DataRequired()], choices=[
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('admin', 'Admin')
    ])
    
    department_id = SelectField('Department', validators=[DataRequired()], coerce=int)
    
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, max=60)
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    
    submit = SubmitField('Submit')
    
    def __init__(self, *args, **kwargs):
        """Initialize form."""
        super(UserForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [
            (dept.id, dept.name) for dept in Department.query.order_by('name')
        ]
    
    def validate_email(self, field):
        """Validate email is unique."""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
