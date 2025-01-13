"""Flask extensions module."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import session
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Initialize security extensions
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Make extensions available at module level
__all__ = [
    'db',
    'migrate',
    'login_manager',
    'csrf',
    'limiter',
    'init_extensions'
]

def init_extensions(app):
    """Initialize Flask extensions."""
    # Initialize SQLAlchemy and Migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize other extensions
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Configure CSRF protection
    @app.before_request
    def csrf_protect():
        if not session.get('csrf_token'):
            session['csrf_token'] = generate_csrf()
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
