from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from .hardware.controller import HardwareController
import logging
import os
from datetime import timedelta
from flask import redirect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    if not app.debug:
        try:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = logging.FileHandler('logs/app.log')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Application startup')
        except Exception as e:
            app.logger.error(f'Error setting up logging: {e}')

    # Initialize extensions
    from .extensions import init_extensions
    init_extensions(app)

    # Register blueprints with URL prefixes
    from .routes import auth_bp, lecturer_bp, student_bp, admin_bp, main_bp
    app.register_blueprint(main_bp)  # No prefix for main routes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Initialize hardware controller
    app.hardware_controller = HardwareController()

    return app
