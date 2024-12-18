from app import db, create_app
from app.models.user import User
from app.models.department import Department

app = create_app()
with app.app_context():
    # Get Computer Science department
    cs_dept = Department.query.filter_by(code='CSC').first()
    
    # Create admin user
    admin = User(
        name='System Administrator',
        email='admin@unilorin.edu.ng',
        user_id='ADMIN001',
        role='admin',
        department_id=cs_dept.id if cs_dept else None
    )
    admin.set_password('admin123')  # Default password
    
    # Check if admin already exists
    existing_admin = User.query.filter_by(user_id='ADMIN001').first()
    if not existing_admin:
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
        print("Login credentials:")
        print("Email: admin@unilorin.edu.ng")
        print("Password: admin123")
    else:
        print("Admin user already exists")
