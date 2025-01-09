from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.models.course import Course
from app.models.attendance import Attendance
from app.models.lecture import Lecture
from app.models.user import User
from app import db
from datetime import datetime, date, timedelta

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('You must be logged in as a student to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    # Get current time
    current_time = datetime.now()
    today = date.today()
    
    # Get student's enrolled courses
    courses = current_user.enrolled_courses.all()
    total_courses = len(courses)
    
    # Get attendance statistics
    total_lectures = 0
    attended_lectures = 0
    
    for course in courses:
        course_lectures = course.lectures.count()
        total_lectures += course_lectures
        attended = Attendance.query.join(Attendance.lecture).filter(
            Attendance.student_id == current_user.id,
            Attendance.status == 'present'
        ).count()
        attended_lectures += attended
    
    attendance_rate = (attended_lectures / total_lectures * 100) if total_lectures > 0 else 0
    
    # Get today's schedule
    today_schedule = Lecture.query.join(Course).filter(
        Course.id.in_([c.id for c in courses]),
        Lecture.date == today
    ).order_by(Lecture.start_time).all()
    
    # Get recent attendance records
    recent_attendance = Attendance.query.join(Attendance.lecture).join(Lecture.course).filter(
        Attendance.student_id == current_user.id
    ).order_by(Lecture.date.desc(), Lecture.start_time.desc()).limit(5).all()
    
    return render_template('student/dashboard.html',
                         current_time=current_time,
                         courses=courses,
                         total_courses=total_courses,
                         total_lectures=total_lectures,
                         attended_lectures=attended_lectures,
                         attendance_rate=attendance_rate,
                         today_schedule=today_schedule,
                         recent_attendance=recent_attendance)

@student_bp.route('/courses')
@login_required
@student_required
def courses():
    courses = current_user.enrolled_courses.all()
    return render_template('student/courses.html', courses=courses)

@student_bp.route('/attendance')
@login_required
@student_required
def attendance():
    courses = current_user.enrolled_courses.all()
    course_attendance = []
    
    for course in courses:
        total_lectures = course.lectures.count()
        attended = Attendance.query.join(Attendance.lecture).filter(
            Attendance.student_id == current_user.id,
            Attendance.status == 'present'
        ).count()
        attendance_rate = (attended / total_lectures * 100) if total_lectures > 0 else 0
        
        course_attendance.append({
            'course': course,
            'total_lectures': total_lectures,
            'attended': attended,
            'attendance_rate': attendance_rate
        })
    
    return render_template('student/attendance.html', course_attendance=course_attendance)

@student_bp.route('/profile')
@login_required
@student_required
def profile():
    return render_template('student/profile.html')
