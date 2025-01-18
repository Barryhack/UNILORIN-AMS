"""Flask configuration."""
import os
from datetime import timedelta

def get_database_url():
    """Get database URI with proper handling of postgres://."""
    uri = os.environ.get('DATABASE_URL')
    if uri and uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)
    return uri or 'postgresql://postgres:postgres@localhost:5432/attendance_system'

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_ENV = 'development'
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # Disable all caching
    CACHE_TYPE = "null"
    CACHE_NO_NULL_WARNING = True
    
    # Template settings
    EXPLAIN_TEMPLATE_LOADING = True
    
    # Database
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 60
    SQLALCHEMY_POOL_RECYCLE = 1800
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_COOKIE_SECURE = False  # Changed to False for development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = 'csrf-key-change-in-production'
    WTF_CSRF_TIME_LIMIT = None  # Disable CSRF token timeout
    WTF_CSRF_SSL_STRICT = False  # Changed to False for development
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
    }
    
    # Development specific
    DEBUG = True
    PROPAGATE_EXCEPTIONS = True

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False
    SECURITY_HEADERS = {}
    RATELIMIT_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SECURITY_HEADERS = {
        **Config.SECURITY_HEADERS,
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data: https:; connect-src 'self'",
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Resource-Policy': 'same-origin'
    }
    LOG_LEVEL = 'INFO'
    PROPAGATE_EXCEPTIONS = True
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = "100 per hour"
    SERVER_NAME = os.environ.get('SERVER_NAME')
    PREFERRED_URL_SCHEME = 'https'
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 60
    SQLALCHEMY_POOL_RECYCLE = 1800
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = True
    RATELIMIT_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
