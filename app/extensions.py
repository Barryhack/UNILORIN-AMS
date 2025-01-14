"""Flask extensions module."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

def init_extensions(app):
    """Initialize Flask extensions."""
    try:
        # Initialize SQLAlchemy first
        db.init_app(app)
        
        # Initialize Flask-Migrate
        migrate.init_app(app, db)
        
        # Initialize other extensions
        login_manager.init_app(app)
        limiter.init_app(app)
        csrf.init_app(app)
        
        # Configure login
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Please log in to access this page.'
        login_manager.login_message_category = 'info'
        
        @login_manager.user_loader
        def load_user(user_id):
            """Load user by ID."""
            from .models import User
            return User.query.get(int(user_id))
        
        # Import models to ensure they are registered with SQLAlchemy
        with app.app_context():
            from .models import (
                User, Course, Department, Attendance, CourseStudent,
                LoginLog, ActivityLog, Notification, Lecture
            )
            
            # Check if database tables exist
            try:
                # Try to query the users table
                db.session.execute(text('SELECT 1 FROM users')).fetchone()
                logger.info("Database tables already exist")
            except Exception as e:
                logger.info("Creating database tables")
                # Create all tables
                db.create_all()
                logger.info("Database tables created successfully")
            
            try:
                # Create default users if they don't exist
                User.create_default_users()
                logger.info("Default users created successfully")
            except Exception as e:
                logger.error(f"Error creating default users: {str(e)}")
                db.session.rollback()
                raise
        
        logger.info('All extensions initialized successfully')
        
    except Exception as e:
        logger.error(f'Error initializing extensions: {str(e)}')
        raise
    
    return None
