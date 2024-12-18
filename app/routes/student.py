from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from app.models.course import Course
from app.models.attendance import Attendance
from app.models.student import Student
from app import db
from datetime import datetime

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/student/dashboard')
@login_required
@student_required
def dashboard():
    # Get student record
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return render_template('student/dashboard.html', courses=[], total_lectures=0, attended_lectures=0, attendance_rate=0)
    
    # Get student's courses
    courses = student.courses
    
    # Get attendance statistics
    total_lectures = 0
    attended_lectures = 0
    
    for course in courses:
        course_lectures = course.lectures.count()
        total_lectures += course_lectures
        attended = Attendance.query.join(Attendance.lecture).filter(
            Attendance.student_id == student.id,
            Attendance.status == 'present'
        ).count()
        attended_lectures += attended
    
    attendance_rate = (attended_lectures / total_lectures * 100) if total_lectures > 0 else 0
    
    return render_template('student/dashboard.html',
                         courses=courses,
                         total_lectures=total_lectures,
                         attended_lectures=attended_lectures,
                         attendance_rate=attendance_rate)

@student_bp.route('/student/courses')
@login_required
@student_required
def courses():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return render_template('student/courses.html', courses=[])
    return render_template('student/courses.html', courses=student.courses)

@student_bp.route('/student/attendance')
@login_required
@student_required
def attendance():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return render_template('student/attendance.html', attendance_records=[])
    attendance_records = Attendance.query.filter_by(student_id=student.id).all()
    return render_template('student/attendance.html', attendance_records=attendance_records)

@student_bp.route('/student/profile')
@login_required
@student_required
def profile():
    student = Student.query.filter_by(user_id=current_user.id).first()
    return render_template('student/profile.html', student=student)
