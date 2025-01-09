from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange, Length
from app.forms import BaseForm

class SystemSettingsForm(BaseForm):
    system_name = StringField('System Name', validators=[
        DataRequired(),
        Length(min=3, max=100, message='System name must be between 3 and 100 characters')
    ])
    
    academic_year = StringField('Academic Year', validators=[
        DataRequired(),
        Length(min=4, max=20, message='Academic year must be in format YYYY/YYYY')
    ])
    
    semester = SelectField('Semester', choices=[
        ('First', 'First Semester'),
        ('Second', 'Second Semester'),
        ('Third', 'Third Semester')
    ], validators=[DataRequired()])
    
    late_threshold = IntegerField('Late Threshold (minutes)', validators=[
        DataRequired(),
        NumberRange(min=1, max=60, message='Late threshold must be between 1 and 60 minutes')
    ])
    
    attendance_threshold = IntegerField('Attendance Threshold (%)', validators=[
        DataRequired(),
        NumberRange(min=0, max=100, message='Attendance threshold must be between 0 and 100 percent')
    ])
