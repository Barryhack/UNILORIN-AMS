from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user

def prevent_authenticated(f):
    """Prevent authenticated users from accessing certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def check_confirmed(f):
    """Ensure user has confirmed their email before accessing route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_confirmed:
            flash('Please confirm your account first.', 'warning')
            return redirect(url_for('auth.unconfirmed'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    """Restrict access based on user roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.role in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def active_user_required(f):
    """Ensure user account is active"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_active:
            flash('Your account has been deactivated. Please contact the administrator.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
