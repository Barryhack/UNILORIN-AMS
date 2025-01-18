"""Main routes for the application."""
from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.extensions import db
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.department import Department
from app.models.activity_log import ActivityLog
import logging
import psutil
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirect to appropriate dashboard based on user role."""
    try:
        if not current_user.is_authenticated:
            logger.info("Unauthenticated user redirected to login")
            return redirect(url_for('auth.login'))
        
        # Log access
        logger.info(f"User {current_user.email} accessing index route")
        
        # Check user role and redirect accordingly
        if current_user.role == 'admin':
            logger.info(f"Admin user {current_user.email} redirected to admin dashboard")
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'lecturer':
            logger.info(f"Lecturer {current_user.email} redirected to lecturer dashboard")
            return redirect(url_for('lecturer.dashboard'))
        elif current_user.role == 'student':
            logger.info(f"Student {current_user.email} redirected to student dashboard")
            return redirect(url_for('student.dashboard'))
        else:
            logger.error(f"Invalid role '{current_user.role}' for user {current_user.email}")
            return render_template('error.html', error="Invalid user role. Please contact administrator."), 400
            
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('error.html', error="An error occurred. Please try again later."), 500

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard route."""
    try:
        # Get basic stats
        stats = {
            'user_count': User.query.count(),
            'active_sessions': User.query.filter_by(is_active=True).count()
        }
        
        # Log access
        logger.info(f"User {current_user.email} accessed dashboard")
        
        if current_user.role == 'lecturer':
            # Get lecturer's courses
            courses = Course.query.filter_by(lecturer_id=current_user.id).all()
            
            # Get recent lectures
            recent_lectures = (Lecture.query
                             .filter_by(lecturer_id=current_user.id)
                             .order_by(Lecture.created_at.desc())
                             .limit(5)
                             .all())
            
            return render_template('staff/dashboard.html',
                                stats=stats,
                                courses=courses,
                                recent_lectures=recent_lectures)
        
        elif current_user.role == 'student':
            # Get student's courses
            enrolled_courses = current_user.enrolled_courses.all()
            
            # Get recent attendance
            recent_attendance = (ActivityLog.query
                               .filter_by(user_id=current_user.id)
                               .order_by(ActivityLog.timestamp.desc())
                               .limit(5)
                               .all())
            
            return render_template('student/dashboard.html',
                                stats=stats,
                                courses=enrolled_courses,
                                recent_attendance=recent_attendance)
        
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        
        else:
            logger.warning(f"User {current_user.email} has invalid role: {current_user.role}")
            return render_template('error.html', error="Invalid user role"), 400
            
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        return render_template('error.html', error="An error occurred. Please try again later."), 500

@main_bp.route('/profile')
@login_required
def profile():
    """User profile route."""
    try:
        return render_template('profile.html', user=current_user)
    except Exception as e:
        logger.error(f"Error in profile route: {str(e)}")
        return render_template('error.html', error="An error occurred. Please try again later."), 500
