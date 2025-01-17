"""Flask application factory."""
from flask import Flask, request, redirect
from config import Config
from .hardware.controller import init_hardware
import logging
import sys
import os
from datetime import datetime, timedelta
from .extensions import db, init_extensions, migrate

def create_app(config_class=Config):
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Force disable template caching
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.cache = {}
    app.jinja_env.auto_reload = True
    app.jinja_env.globals.update(now=datetime.now)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Add file logging in production
    if not app.debug:
        try:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = logging.FileHandler('logs/app.log')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s]: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            # Also add stderr handler for errors
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s]: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            stderr_handler.setLevel(logging.ERROR)
            app.logger.addHandler(stderr_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info('Application startup')
        except Exception as e:
            print(f'Error setting up logging: {e}', file=sys.stderr)

    # Initialize extensions
    init_extensions(app)

    # Initialize hardware controller
    with app.app_context():
        try:
            init_hardware()
            app.logger.info('Hardware controller initialized')
        except Exception as e:
            app.logger.error(f'Error initializing hardware controller: {e}')

    # Initialize database and create default users
    with app.app_context():
        try:
            # Run migrations instead of create_all()
            migrate.init_app(app, db)
            from .models import User
            User.create_default_users()
        except Exception as e:
            app.logger.error(f'Error initializing database: {e}')

    # Register blueprints with URL prefixes
    from .routes import auth_bp, lecturer_bp, student_bp, admin_bp, main_bp
    app.register_blueprint(main_bp)  # No prefix for main routes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
