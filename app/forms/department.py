"""Department forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from ..models import Department

class DepartmentForm(FlaskForm):
    """Form for creating/editing departments."""
    
    name = StringField('Department Name', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    
    description = TextAreaField('Description', validators=[
        Length(max=500)
    ])
    
    submit = SubmitField('Submit')
    
    def validate_name(self, field):
        """Validate department name is unique."""
        dept = Department.query.filter_by(name=field.data).first()
        if dept:
            raise ValidationError('Department name already exists.')
