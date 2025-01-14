"""Flask extensions module."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import logging

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
        
        # Import models to ensure they are registered with SQLAlchemy
        with app.app_context():
            from .models import (
                User, Course, Department, Attendance, CourseStudent,
                LoginLog, ActivityLog, Notification, Lecture
            )
            
            # Create all tables
            db.create_all()
            
            # Create default users if they don't exist
            User.create_default_users()
        
        # Initialize other extensions
        migrate.init_app(app, db)
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
        
        logger.info('All extensions initialized successfully')
        
    except Exception as e:
        logger.error(f'Error initializing extensions: {str(e)}')
        raise
    
    return None
