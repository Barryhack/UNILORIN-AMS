from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Create a test user
    test_user = User(
        user_id='ADMIN123',
        name='System Administrator',
        email='admin@unilorin.edu.ng',
        role='admin'
    )
    test_user.set_password('password123')
    
    try:
        # Add to database
        db.session.add(test_user)
        db.session.commit()
        
        print("Test user created successfully!")
        print("Login with:")
        print("Email/ID: admin@unilorin.edu.ng or ADMIN123")
        print("Password: password123")
    except Exception as e:
        print(f"Error creating test user: {e}")
        db.session.rollback()
