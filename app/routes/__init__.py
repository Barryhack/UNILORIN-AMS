from flask import Blueprint

# Import all route blueprints
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.lecturer import lecturer_bp
from app.routes.student import student_bp

def register_blueprints(app):
    """Initialize all route blueprints with the app"""
    
    # Register blueprints
    app.register_blueprint(main_bp)  # Root routes
    app.register_blueprint(auth_bp)  # Auth routes (login/logout)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')
    app.register_blueprint(student_bp, url_prefix='/student')
