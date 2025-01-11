from app.extensions import db
from datetime import datetime

class Department(db.Model):
    """Department model for storing department related details."""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department_users = db.relationship('User', back_populates='department')
    courses = db.relationship('Course', back_populates='department', lazy='dynamic')

    def __init__(self, name, code, description=None):
        self.name = name
        self.code = code
        self.description = description

    def __repr__(self):
        return f'<Department {self.name}>'

# Create default departments if they don't exist
def create_default_departments():
    """Create default departments if they don't exist."""
    try:
        # Computer Science Department
        if not Department.query.filter_by(code='CSC').first():
            cs_dept = Department(
                name='Computer Science',
                code='CSC',
                description='Department of Computer Science'
            )
            db.session.add(cs_dept)

        # Engineering Department
        if not Department.query.filter_by(code='ENG').first():
            eng_dept = Department(
                name='Engineering',
                code='ENG',
                description='Department of Engineering'
            )
            db.session.add(eng_dept)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default departments: {e}")
