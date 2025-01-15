"""Flask extensions module."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import logging
from sqlalchemy import text, event
import os
import time

logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

def init_db_schema(app):
    """Initialize database schema with retries."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                # First terminate all existing connections
                db.session.execute(text('''
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                    AND pid <> pg_backend_pid()
                    AND state in ('idle', 'idle in transaction', 'idle in transaction (aborted)', 'disabled')
                '''))
                db.session.commit()
                
                # Set statement timeout to avoid indefinite locks
                db.session.execute(text('SET statement_timeout = 30000'))  # 30 seconds
                
                # Drop and recreate schema
                db.session.execute(text('''
                    DROP SCHEMA IF EXISTS public CASCADE;
                    CREATE SCHEMA public;
                    GRANT ALL ON SCHEMA public TO postgres;
                    GRANT ALL ON SCHEMA public TO public;
                '''))
                db.session.commit()
                
                # Run migrations
                from flask_migrate import upgrade
                upgrade()
                
                logger.info("Database schema initialized successfully")
                return True
                
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            db.session.rollback()
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Database initialization failed.")
                raise
    
    return False

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
                LoginLog, ActivityLog, Notification, Lecture, HardwareStatus
            )
            
            try:
                # Initialize database schema
                logger.info("Initializing database schema")
                init_db_schema(app)
                logger.info("Database initialization completed successfully")
                
            except Exception as e:
                logger.error(f"Error during database initialization: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Error initializing extensions: {e}")
        raise
