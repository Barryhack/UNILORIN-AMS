from app import create_app, db
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

def create_admin_user():
    """Create admin user if it doesn't exist"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if admin user exists
            admin = User.query.filter_by(id_number='19/52AD001').first()
            if admin:
                print("Admin user already exists")
                # Update admin password
                admin.set_password('Admin@2024')
                db.session.commit()
                print("Admin password updated")
                return
            
            # Create admin user
            admin = User(
                name='Administrator',
                email='admin@unilorin.edu.ng',
                role='admin',
                id_number='19/52AD001'
            )
            admin.set_password('Admin@2024')
            db.session.add(admin)
            db.session.commit()
            print("Created admin user successfully")
            
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_admin_user()
