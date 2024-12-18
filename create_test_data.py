from app import db, create_app
from app.models.department import Department

app = create_app()
with app.app_context():
    # Create test departments
    departments = [
        Department(name='Computer Science', code='CSC'),
        Department(name='Electrical Engineering', code='EEE'),
        Department(name='Mechanical Engineering', code='MEE'),
        Department(name='Civil Engineering', code='CVE')
    ]
    
    for dept in departments:
        existing = Department.query.filter_by(code=dept.code).first()
        if not existing:
            db.session.add(dept)
    
    db.session.commit()
    print("Test departments created successfully!")
