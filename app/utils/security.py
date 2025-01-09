from functools import wraps
from flask import current_app, request, abort, session
from datetime import datetime, timedelta
import secrets
import bcrypt
import re
import logging
from urllib.parse import urlparse, urljoin
import os

logger = logging.getLogger(__name__)

def add_security_headers(response):
    """Add security headers to the response"""
    # Prevent browsers from performing MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable browser's XSS filtering
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Prevent all iframe embedding except from same origin
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Enable HSTS (HTTP Strict Transport Security)
    if not current_app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # Content Security Policy with better security and flexibility
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'self'; "
        "form-action 'self'; "
        "base-uri 'self'; "
        "object-src 'none'"
    )
    response.headers['Content-Security-Policy'] = csp
    
    # Permissions Policy (formerly Feature-Policy)
    response.headers['Permissions-Policy'] = (
        'geolocation=(), '
        'microphone=(), '
        'camera=()'
    )
    
    return response

def require_2fa(f):
    """Decorator to require 2FA for sensitive routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('2fa_verified'):
            logger.warning(f"2FA verification required for {request.path}")
            return abort(403, description="Two-factor authentication required")
        return f(*args, **kwargs)
    return decorated_function

def validate_ip(ip_address):
    """Validate IP address format"""
    import ipaddress
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False

def get_client_ip():
    """Get client IP address from request with additional validation"""
    forwarded_for = request.headers.getlist("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for[0]
        # Validate the forwarded IP
        if validate_ip(ip):
            return ip
    return request.remote_addr

def is_safe_url(target):
    """Validate URL to prevent open redirect vulnerabilities"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def sanitize_filename(filename):
    """Sanitize a filename to prevent path traversal attacks"""
    # Remove any directory components
    filename = re.sub(r'[/\\]', '', filename)
    # Remove any null bytes
    filename = filename.replace('\0', '')
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length-len(ext)] + ext
    return filename

def generate_random_string(length=32):
    """Generate a cryptographically secure random string"""
    return secrets.token_urlsafe(length)

def hash_password(password):
    """Hash a password using bcrypt with proper salt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt)

def verify_password(password_hash, password):
    """Verify a password against its hash using constant-time comparison"""
    try:
        return bcrypt.checkpw(password.encode(), password_hash)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def rate_limit_exceeded_handler():
    """Handler for rate limit exceeded"""
    logger.warning(f"Rate limit exceeded for IP: {get_client_ip()}")
    response = {
        'error': 'Too many requests',
        'retry_after': 60
    }
    return response, 429

def check_password_strength(password):
    """Check password strength against security requirements"""
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password meets security requirements"

def generate_csrf_token():
    """Generate a new CSRF token"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = generate_random_string()
    return session['_csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token"""
    stored_token = session.get('_csrf_token')
    if not stored_token or not token or stored_token != token:
        logger.warning("CSRF token validation failed")
        return False
    return True
