from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from config import Config
from .hardware.controller import HardwareController
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from datetime import timedelta
from flask import redirect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
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

    with app.app_context():
        # Initialize extensions
        db.init_app(app)
        migrate.init_app(app, db)
        login_manager.init_app(app)
        csrf.init_app(app)
        mail.init_app(app)
        limiter.init_app(app)
        
        # Initialize hardware controller
        app.hardware_controller = HardwareController()

        # Set up login view
        login_manager.login_view = 'auth.login'
        login_manager.login_message_category = 'info'

        # Register blueprints
        from app.routes import register_blueprints
        register_blueprints(app)

        # Create tables
        db.create_all()

    return app
