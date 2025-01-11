from flask import Blueprint, render_template, redirect, url_for, request
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
    if not current_user.is_authenticated:
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(url_for('auth.login', next=next_page))
        
    # Redirect to appropriate dashboard based on user role
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'lecturer':
        return redirect(url_for('lecturer.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get basic stats
        user_count = User.query.count()
        active_sessions = User.query.filter_by(is_active=True).count()
        
        # Log access
        logger.info(f"User {current_user.email} accessed dashboard")
        
        if current_user.role == 'lecturer':
            # Get lecturer's courses
            courses = Course.query.filter_by(lecturer_id=current_user.id).all()
            
            # Get recent lectures
            recent_lectures = Lecture.query.filter_by(lecturer_id=current_user.id)\
                .order_by(Lecture.created_at.desc())\
                .limit(5)\
                .all()
            
            # Get system information
            system_info = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': psutil.virtual_memory()._asdict(),
                'disk': psutil.disk_usage('/')._asdict()
            }
            
            return render_template('staff/dashboard.html',
                                 courses=courses,
                                 recent_lectures=recent_lectures,
                                 system_info=system_info,
                                 user_count=user_count,
                                 active_sessions=active_sessions)
        elif current_user.role == 'student':
            # Get student's enrolled courses
            courses = current_user.enrolled_courses
            
            # Get recent attendance records
            recent_attendance = current_user.attendances\
                .order_by(Attendance.created_at.desc())\
                .limit(5)\
                .all()
            
            return render_template('student/dashboard.html',
                                 courses=courses,
                                 recent_attendance=recent_attendance,
                                 user_count=user_count,
                                 active_sessions=active_sessions)
        else:
            return render_template('dashboard.html',
                                 user_count=user_count,
                                 active_sessions=active_sessions)
    except Exception as e:
        logger.error(f"Error accessing dashboard: {str(e)}")
        return render_template('dashboard.html')

@main_bp.route('/profile')
@login_required
def profile():
    # Get user's activity logs
    activity_logs = ActivityLog.query.filter_by(
        user_id=current_user.id
    ).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    # Get attendance stats if user is a student
    attendance_stats = None
    if current_user.role == 'student':
        total_lectures = 0
        attended_lectures = 0
        for course in current_user.enrolled_courses:
            course_lectures = course.lectures.count()
            total_lectures += course_lectures
            attended_lectures += Attendance.query.join(
                Course, Course.id == Attendance.course_id
            ).filter(
                Attendance.user_id == current_user.id,
                Attendance.status == 'present',
                Course.id == course.id
            ).count()
            
        attendance_stats = {
            'total_lectures': total_lectures,
            'attended_lectures': attended_lectures,
            'attendance_rate': (attended_lectures / total_lectures * 100) if total_lectures > 0 else 0
        }
    
    return render_template('profile.html',
                         user=current_user,
                         activity_logs=activity_logs,
                         attendance_stats=attendance_stats)
