from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class SystemSettingsForm(FlaskForm):
    system_name = StringField('System Name', validators=[DataRequired()])
    academic_year = StringField('Academic Year', validators=[DataRequired()])
    semester = SelectField('Semester', choices=[('First', 'First Semester'), ('Second', 'Second Semester')])
    late_threshold = IntegerField('Late Threshold (minutes)', 
                                validators=[DataRequired(), NumberRange(min=1, max=60)],
                                default=15)
    attendance_threshold = IntegerField('Minimum Attendance Percentage',
                                      validators=[DataRequired(), NumberRange(min=0, max=100)],
                                      default=75)
