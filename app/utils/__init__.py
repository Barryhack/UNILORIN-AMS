"""Utils package."""
from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user

def admin_required(f):
    """Ensure user is an admin before accessing route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Import and expose other utils
from .decorators import (
    prevent_authenticated,
    check_confirmed,
    roles_required,
    active_user_required
)

__all__ = [
    'admin_required',
    'prevent_authenticated',
    'check_confirmed',
    'roles_required',
    'active_user_required'
]
