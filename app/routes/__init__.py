from flask import Blueprint

# Import all route blueprints
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.lecturer import lecturer_bp
from app.routes.student import student_bp

def init_routes(app):
    """Initialize all route blueprints with the app"""
    
    # Register blueprints
    app.register_blueprint(main_bp)  # Root routes
    app.register_blueprint(auth_bp)  # Auth routes (login/logout)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')
    app.register_blueprint(student_bp, url_prefix='/student')
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to response"""
        # Prevent browsers from performing MIME-type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Protection against clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Enable browser's XSS filter
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Enable strict HTTPS (for production, comment out during development)
        # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Control browser features and APIs
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy
        csp = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com",
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
            "img-src 'self' data: https:",
            "connect-src 'self' ws: wss:",  # Allow WebSocket connections
            "frame-ancestors 'self'",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'"
        ]
        response.headers['Content-Security-Policy'] = "; ".join(csp)
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    # Add CSRF protection headers
    @app.after_request
    def add_csrf_headers(response):
        if 'csrf_token' not in response.headers:
            response.headers['X-CSRF-Token'] = app.jinja_env.globals['csrf_token']()
        return response

    return app
