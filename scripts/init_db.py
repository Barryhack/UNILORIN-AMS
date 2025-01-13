"""Manual database initialization script."""
import os
import sys
from sqlalchemy import text

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from config import ProductionConfig

def init_database():
    """Initialize the database with proper schema."""
    app = create_app(ProductionConfig)
    
    with app.app_context():
        # Drop all tables first
        db.drop_all()
        print("Dropped all existing tables")
        
        # Create all tables
        db.create_all()
        print("Created all tables")
        
        # Verify the users table structure
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
            columns = [row[0] for row in result]
            print(f"Users table columns: {columns}")
            
            if 'login_id' not in columns:
                print("ERROR: login_id column is missing from users table")
                sys.exit(1)
        
        # Create default users
        from app.models import User
        User.create_default_users()
        print("Created default users")
        
        print("Database initialization completed successfully!")

if __name__ == '__main__':
    init_database()
