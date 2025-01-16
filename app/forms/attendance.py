"""Attendance forms."""
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, SubmitField
from wtforms.validators import DataRequired
from ..models import Course, User

class AttendanceForm(FlaskForm):
    """Form for recording attendance."""
    
    course_id = SelectField('Course', validators=[DataRequired()], coerce=int)
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
    def __init__(self, *args, **kwargs):
        """Initialize form."""
        super(AttendanceForm, self).__init__(*args, **kwargs)
        self.course_id.choices = [
            (course.id, f"{course.code} - {course.title}") 
            for course in Course.query.order_by('code')
        ]
