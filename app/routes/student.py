from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.attendance import Attendance
from datetime import datetime

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('You must be a student to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    # Get current time
    current_time = datetime.now()

    # Get quick stats
    stats = {
        'total_courses': len(current_user.enrolled_courses),
        'total_lectures_attended': Attendance.query.filter_by(
            student_id=current_user.id,
            status='present'
        ).count(),
        'total_lectures': sum([
            Lecture.query.filter_by(course_id=course.id).count()
            for course in current_user.enrolled_courses
        ]),
        'attendance_rate': 0  # Will be calculated below
    }

    # Calculate attendance rate
    if stats['total_lectures'] > 0:
        stats['attendance_rate'] = (stats['total_lectures_attended'] / stats['total_lectures']) * 100

    # Get today's lectures
    today_lectures = Lecture.query.join(Course).join(
        'enrolled_students'
    ).filter(
        Course.enrolled_students.any(id=current_user.id),
        Lecture.date == current_time.date()
    ).order_by(Lecture.start_time).all()

    # Get recent attendance records
    recent_attendance = Attendance.query.filter_by(
        student_id=current_user.id
    ).order_by(Attendance.timestamp.desc()).limit(10).all()

    return render_template('student/dashboard.html',
                         stats=stats,
                         today_lectures=today_lectures,
                         recent_attendance=recent_attendance)

@student_bp.route('/courses')
@login_required
@student_required
def courses():
    return render_template('student/courses.html', 
                         courses=current_user.enrolled_courses)

@student_bp.route('/attendance')
@login_required
@student_required
def attendance():
    # Get attendance records for all courses
    attendance_records = Attendance.query.join(Lecture).join(Course).filter(
        Attendance.student_id == current_user.id
    ).order_by(Lecture.date.desc()).all()
    
    return render_template('student/attendance.html', 
                         attendance_records=attendance_records)

@student_bp.route('/reports')
@login_required
@student_required
def reports():
    return render_template('student/reports.html')

@student_bp.route('/profile')
@login_required
@student_required
def profile():
    return render_template('student/profile.html')

@student_bp.route('/settings')
@login_required
@student_required
def settings():
    return render_template('student/settings.html')
