from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.attendance import Attendance
from app.models.student import Student
from app import db
from datetime import datetime, date
from sqlalchemy import func

lecturer_bp = Blueprint('lecturer', __name__)

def lecturer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'lecturer':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@lecturer_bp.route('/lecturer/dashboard')
@login_required
@lecturer_required
def dashboard():
    # Get courses taught by the lecturer
    courses = Course.query.join(Lecture).filter(Lecture.lecturer_id == current_user.id).all()
    
    # Get total number of students across all courses
    total_students = db.session.query(func.count(Student.id.distinct()))\
        .join(Course.students)\
        .join(Lecture)\
        .filter(Lecture.lecturer_id == current_user.id)\
        .scalar() or 0

    # Get today's classes
    today = datetime.now().date()
    today_classes = Lecture.query\
        .filter(Lecture.lecturer_id == current_user.id)\
        .filter(db.func.date(Lecture.date) == today)\
        .count()

    # Calculate average attendance rate
    attendance_rate = 0
    total_records = 0
    present_records = 0
    
    for course in courses:
        records = Attendance.query.filter_by(course_id=course.id).all()
        total_records += len(records)
        present_records += len([r for r in records if r.status == 'present'])
    
    if total_records > 0:
        attendance_rate = (present_records / total_records) * 100

    return render_template('lecturer/dashboard.html',
                         courses=courses,
                         total_students=total_students,
                         today_classes=today_classes,
                         attendance_rate=attendance_rate)

@lecturer_bp.route('/lecturer/courses')
@login_required
@lecturer_required
def courses():
    # Get courses taught by the lecturer
    courses = Course.query.join(Lecture).filter(Lecture.lecturer_id == current_user.id).all()
    return render_template('lecturer/courses.html', courses=courses)

@lecturer_bp.route('/lecturer/courses/<int:course_id>')
@login_required
@lecturer_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    # Verify that the lecturer teaches this course
    lecture = Lecture.query.filter_by(course_id=course_id, lecturer_id=current_user.id).first()
    if not lecture:
        abort(403)
    return render_template('lecturer/view_course.html', course=course)

@lecturer_bp.route('/lecturer/courses/<int:course_id>/attendance')
@login_required
@lecturer_required
def course_attendance(course_id):
    course = Course.query.get_or_404(course_id)
    # Verify that the lecturer teaches this course
    lecture = Lecture.query.filter_by(course_id=course_id, lecturer_id=current_user.id).first()
    if not lecture:
        abort(403)
    # Get attendance records for this course
    attendance_records = Attendance.query.filter_by(course_id=course_id).all()
    return render_template('lecturer/course_attendance.html', course=course, attendance_records=attendance_records)

@lecturer_bp.route('/lecturer/attendance')
@login_required
@lecturer_required
def attendance():
    # Get all courses taught by the lecturer
    courses = Course.query.join(Lecture).filter(Lecture.lecturer_id == current_user.id).all()
    # Get attendance records for all courses
    attendance_records = []
    for course in courses:
        records = Attendance.query.filter_by(course_id=course.id).all()
        attendance_records.extend(records)
    return render_template('lecturer/attendance.html', attendance_records=attendance_records)
