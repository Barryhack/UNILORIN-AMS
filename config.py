import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
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
    DEBUG = False
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True
    
    # Server name for URL generation
    SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost:5000')
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/app.log'
    
    # Login settings
    LOGIN_DISABLED = False
    LOGIN_VIEW = 'auth.login'
    LOGIN_MESSAGE = 'Please log in to access this page.'
    LOGIN_MESSAGE_CATEGORY = 'info'
    
    # Rate limiting
    RATELIMIT_DEFAULT = "1000 per day;200 per hour;10 per second"
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_STRATEGY = "fixed-window"

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
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # Reduced from 1 hour for security
    
    # Enhanced security headers
    SECURITY_HEADERS = {
        **Config.SECURITY_HEADERS,
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data: https:; connect-src 'self';",
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Resource-Policy': 'same-origin'
    }
    
    # Logging and error handling
    LOG_LEVEL = 'ERROR'
    PROPAGATE_EXCEPTIONS = False
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Server and SSL
    SERVER_NAME = os.environ.get('SERVER_NAME', 'unilorin-ams-vf9i.onrender.com')
    PREFERRED_URL_SCHEME = 'https'
    
    # Database optimizations
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 30

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
