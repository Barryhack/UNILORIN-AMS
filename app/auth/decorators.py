from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """
    Decorator for views that require admin access.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    """
    Decorator for views that require specific role(s).
    Usage: @roles_required('admin', 'moderator')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized
            if not any(current_user.role == role for role in roles):
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator
