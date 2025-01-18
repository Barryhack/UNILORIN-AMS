"""Flask application factory."""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_migrate import upgrade
from config import config
from .extensions import db, migrate, login_manager, limiter, csrf
from .models import User

def create_app(config_class=None):
    """Create Flask application."""
    app = Flask(__name__)
    
    # Load the configuration
    if config_class is None:
        config_name = os.getenv('FLASK_ENV', 'production')
        config_class = config[config_name]
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Configure logging
    if not app.debug and not app.testing:
        if app.config.get('LOG_TO_STDOUT', False):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/attendance.log',
                                            maxBytes=10240,
                                            backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Attendance System startup')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.lecturer import lecturer_bp
    from .routes.student import student_bp
    from .routes.admin import admin_bp
    from .routes.main import main_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @app.before_first_request
    def before_first_request():
        """Initialize application before first request."""
        # Create database tables if they don't exist
        with app.app_context():
            try:
                db.create_all()
                app.logger.info('Database tables created successfully')
            except Exception as e:
                app.logger.error(f'Error creating database tables: {e}')

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to response."""
        for key, value in app.config.get('SECURITY_HEADERS', {}).items():
            response.headers[key] = value
        return response

    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        """Add objects to shell context."""
        return {'db': db, 'User': User}

    return app
