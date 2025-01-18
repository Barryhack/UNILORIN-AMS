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
from sqlalchemy.exc import DisconnectionError

logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    strategy="fixed-window",
    default_limits=["200 per day", "50 per hour"]
)
csrf = CSRFProtect()

def init_db_schema(app):
    """Initialize database schema with retries."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                # Check if database exists and is accessible
                db.session.execute(text('SELECT 1'))
                db.session.commit()
                logger.info("Database connection successful")

                # Set statement timeout for PostgreSQL
                if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
                    db.session.execute(text('SET statement_timeout = 30000'))  # 30 seconds
                    db.session.commit()
                    logger.info("PostgreSQL settings applied")

                # Initialize tables if they don't exist
                db.create_all()
                logger.info("Database tables created")
                
                return True
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f"All database connection attempts failed: {e}")
                raise
    
    return False

def init_extensions(app):
    """Initialize Flask extensions."""
    try:
        # Initialize SQLAlchemy with engine options
        db.init_app(app)
        logger.info("SQLAlchemy initialized")

        # Initialize Flask-Migrate
        migrate.init_app(app, db)
        logger.info("Flask-Migrate initialized")

        # Initialize Flask-Login with secure settings
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message_category = 'info'
        login_manager.session_protection = 'strong'
        login_manager.refresh_view = 'auth.login'
        login_manager.needs_refresh_message = 'Please login again to confirm your identity'
        login_manager.needs_refresh_message_category = 'info'
        logger.info("Flask-Login initialized")

        # Initialize Flask-Limiter
        limiter.init_app(app)
        logger.info("Flask-Limiter initialized")

        # Initialize CSRF protection with secure settings
        csrf.init_app(app)
        logger.info("CSRF protection initialized")

        # Initialize database schema
        if init_db_schema(app):
            logger.info("Database schema initialized")
        else:
            logger.error("Failed to initialize database schema")

        @login_manager.user_loader
        def load_user(user_id):
            from .models import User
            return User.query.get(int(user_id))
        
        # Import models to ensure they are registered with SQLAlchemy
        with app.app_context():
            from .models import (
                User, Course, Department, Attendance, CourseStudent,
                LoginLog, ActivityLog, Notification, Lecture, HardwareStatus
            )
            
        # Set up database connection pooling for PostgreSQL
        if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
            @event.listens_for(db.engine, 'connect')
            def connect(dbapi_connection, connection_record):
                connection_record.info['pid'] = os.getpid()

            @event.listens_for(db.engine, 'checkout')
            def checkout(dbapi_connection, connection_record, connection_proxy):
                pid = os.getpid()
                if connection_record.info['pid'] != pid:
                    connection_record.connection = connection_proxy.connection = None
                    raise DisconnectionError(
                        "Connection record belongs to pid %s, "
                        "attempting to check out in pid %s" %
                        (connection_record.info['pid'], pid)
                    )

            logger.info("PostgreSQL connection pooling configured")

    except Exception as e:
        logger.error(f"Error initializing extensions: {e}")
        raise
