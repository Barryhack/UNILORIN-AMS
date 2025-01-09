from app import create_app, db
from app.models.user import User, create_default_users
from app.models.department import Department, create_default_departments
from app.models.faculty import Faculty, create_default_faculties
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.attendance import Attendance
from app.models.system_settings import SystemSettings
from app.models.login_log import LoginLog
from app.models.activity_log import ActivityLog
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/init_db.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def init_db(drop_existing=False):
    """Initialize the database with required tables and initial data
    
    Args:
        drop_existing (bool): If True, drops existing database before initialization
    """
    app = create_app()
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if drop_existing and os.path.exists(db_path):
            logger.info("Dropping existing database...")
            db.drop_all()
            logger.info("Database dropped successfully")
        
        # Create instance directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create all tables
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Create default faculties
        logger.info("Creating default faculties...")
        faculty = create_default_faculties()
        logger.info("Default faculties created successfully")
        
        # Create default departments
        logger.info("Creating default departments...")
        departments = create_default_departments()
        logger.info("Default departments created successfully")
        
        # Create default users
        logger.info("Creating default users...")
        create_default_users()
        logger.info("Default users created successfully")
        
        logger.info("Database initialization completed successfully!")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Initialize the database')
    parser.add_argument('--drop', action='store_true', help='Drop existing database before initialization')
    args = parser.parse_args()
    
    init_db(drop_existing=args.drop)
