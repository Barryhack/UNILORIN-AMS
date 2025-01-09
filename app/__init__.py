from flask import Flask, request
from config import Config
from app.extensions import db, login_manager, csrf, socketio, limiter, talisman
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
import click
from datetime import timedelta
from flask import redirect

def create_app(config_class=Config):
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Attendance System startup')
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # Configure WebSocket with secure defaults
    socketio.init_app(app, 
                     cors_allowed_origins=[app.config.get('FRONTEND_URL', '*')],
                     ping_timeout=10,
                     ping_interval=5)
    
    # Initialize Flask-Talisman for security headers
    talisman.init_app(app,
                     force_https=not app.debug,
                     strict_transport_security=True,
                     session_cookie_secure=not app.debug,
                     content_security_policy={
                         'default-src': "'self'",
                         'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'",
                                      'https://cdn.jsdelivr.net',
                                      'https://code.jquery.com',
                                      'https://cdnjs.cloudflare.com'],
                         'style-src': ["'self'", "'unsafe-inline'",
                                     'https://cdn.jsdelivr.net',
                                     'https://fonts.googleapis.com',
                                     'https://cdnjs.cloudflare.com'],
                         'img-src': ["'self'", 'data:', 'https:'],
                         'font-src': ["'self'",
                                    'https://fonts.gstatic.com',
                                    'https://cdnjs.cloudflare.com'],
                         'connect-src': ["'self'", 'ws:', 'wss:']
                     })
    
    # Initialize rate limiter
    limiter.init_app(app)
    
    # Setup login manager with secure defaults
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.refresh_view = 'auth.login'
    login_manager.needs_refresh_message = 'Please reauthenticate to access this page.'
    login_manager.needs_refresh_message_category = 'info'
    login_manager.session_protection = 'strong'
    
    # Configure session security
    app.config.update(
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=60),
        SESSION_COOKIE_SECURE=not app.debug,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_SECURE=not app.debug,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_DURATION=timedelta(days=14)
    )
    
    # Import models
    from app.models.user import User, create_default_users
    from app.models.department import Department
    from app.models.faculty import Faculty
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Register blueprints
    from app.routes import init_routes
    init_routes(app)
    
    # Register error handlers
    from app.handlers import init_error_handlers
    init_error_handlers(app)
    
    # Add security headers to all responses
    from app.utils.security import add_security_headers
    app.after_request(add_security_headers)
    
    # Add rate limiting
    limiter.limit("200/day;50/hour;1/second")(app)
    
    @app.before_request
    def before_request():
        # Require HTTPS in production
        if not app.debug and not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
    
    # Add CLI commands
    @app.cli.command('init-db')
    def init_db():
        """Initialize the database with default data."""
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create default faculty
            faculty = Faculty.query.filter_by(name='Science').first()
            if not faculty:
                faculty = Faculty(
                    name='Science',
                    code='SCI',
                    description='Faculty of Science'
                )
                db.session.add(faculty)
                db.session.commit()
            
            # Create default department
            dept = Department.query.filter_by(name='Computer Science').first()
            if not dept:
                dept = Department(
                    name='Computer Science',
                    code='CSC',
                    faculty_id=faculty.id,
                    description='Department of Computer Science'
                )
                db.session.add(dept)
                db.session.commit()
            
            # Create default users
            create_default_users()
            
            click.echo('Database initialized with default data.')
    
    return app
