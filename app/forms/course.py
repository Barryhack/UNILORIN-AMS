"""Course forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from ..models import Department

class CourseForm(FlaskForm):
    """Form for creating/editing courses."""
    
    code = StringField('Course Code', validators=[
        DataRequired(),
        Length(min=3, max=10)
    ])
    
    title = StringField('Course Title', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    
    description = TextAreaField('Description', validators=[
        Length(max=500)
    ])
    
    department_id = SelectField('Department', validators=[DataRequired()], coerce=int)
    
    submit = SubmitField('Submit')
    
    def __init__(self, *args, **kwargs):
        """Initialize form."""
        super(CourseForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [
            (dept.id, dept.name) for dept in Department.query.order_by('name')
        ]
