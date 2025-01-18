from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.attendance import Attendance
from datetime import datetime, timedelta
from sqlalchemy import func, case

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

    # Get courses and calculate status
    courses = current_user.enrolled_courses
    courses_good = 0
    courses_at_risk = 0
    
    for course in courses:
        attendance_rate = db.session.query(
            func.avg(case([(Attendance.status == 'present', 100)], else_=0))
        ).join(Lecture).filter(
            Lecture.course_id == course.id,
            Attendance.student_id == current_user.id
        ).scalar() or 0
        
        if attendance_rate >= 75:
            courses_good += 1
        else:
            courses_at_risk += 1

    # Calculate attendance streak
    attendance_streak = 0
    current_date = current_time.date()
    
    while True:
        day_attendance = Attendance.query.join(Lecture).filter(
            Lecture.date == current_date,
            Attendance.student_id == current_user.id,
            Attendance.status == 'present'
        ).first()
        
        if not day_attendance:
            break
            
        attendance_streak += 1
        current_date -= timedelta(days=1)

    # Calculate attendance trends
    current_week_attendance = db.session.query(
        func.avg(case([(Attendance.status == 'present', 100)], else_=0))
    ).join(Lecture).filter(
        Attendance.student_id == current_user.id,
        Lecture.date >= current_time.date() - timedelta(days=7),
        Lecture.date <= current_time.date()
    ).scalar() or 0

    last_week_attendance = db.session.query(
        func.avg(case([(Attendance.status == 'present', 100)], else_=0))
    ).join(Lecture).filter(
        Attendance.student_id == current_user.id,
        Lecture.date >= current_time.date() - timedelta(days=14),
        Lecture.date < current_time.date() - timedelta(days=7)
    ).scalar() or 0

    attendance_trend = 0
    if last_week_attendance > 0:
        attendance_trend = current_week_attendance - last_week_attendance

    # Get total lectures and attendance
    total_lectures = sum(
        Lecture.query.filter_by(course_id=course.id).count()
        for course in courses
    )
    
    total_lectures_attended = Attendance.query.filter_by(
        student_id=current_user.id,
        status='present'
    ).count()
    
    lectures_completed = Attendance.query.join(Lecture).filter(
        Attendance.student_id == current_user.id,
        Lecture.end_time < current_time
    ).count()

    # Calculate attendance rate
    attendance_rate = 0
    if total_lectures > 0:
        attendance_rate = (total_lectures_attended / total_lectures) * 100

    # Get today's lectures with status
    today_lectures = []
    raw_lectures = Lecture.query.join(Course).join(
        Course.enrolled_students
    ).filter(
        Course.enrolled_students.any(id=current_user.id),
        Lecture.date == current_time.date()
    ).order_by(Lecture.start_time).all()

    for lecture in raw_lectures:
        attendance = Attendance.query.filter_by(
            lecture_id=lecture.id,
            student_id=current_user.id
        ).first()
        
        lecture_dict = {
            'course': lecture.course,
            'start_time': lecture.start_time,
            'end_time': lecture.end_time,
            'room': lecture.room,
            'lecturer': lecture.lecturer,
            'has_started': lecture.start_time <= current_time,
            'has_ended': lecture.end_time < current_time,
            'attendance_status': attendance.status if attendance else None
        }
        today_lectures.append(lecture_dict)

    # Get upcoming week schedule
    upcoming_week = []
    for i in range(7):
        date = current_time.date() + timedelta(days=i)
        lectures = Lecture.query.join(Course).join(
            Course.enrolled_students
        ).filter(
            Course.enrolled_students.any(id=current_user.id),
            Lecture.date == date
        ).order_by(Lecture.start_time).all()
        
        # Mark important lectures (low attendance courses)
        for lecture in lectures:
            course_attendance = db.session.query(
                func.avg(case([(Attendance.status == 'present', 100)], else_=0))
            ).join(Lecture).filter(
                Lecture.course_id == lecture.course_id,
                Attendance.student_id == current_user.id
            ).scalar() or 0
            
            lecture.is_important = course_attendance < 75
        
        upcoming_week.append({
            'date': date,
            'lectures': lectures
        })

    # Prepare course performance data
    course_performance = []
    for course in courses:
        total_course_lectures = Lecture.query.filter_by(course_id=course.id).count()
        attended_lectures = Attendance.query.join(Lecture).filter(
            Lecture.course_id == course.id,
            Attendance.student_id == current_user.id,
            Attendance.status == 'present'
        ).count()
        
        missed_lectures = Attendance.query.join(Lecture).filter(
            Lecture.course_id == course.id,
            Attendance.student_id == current_user.id,
            Attendance.status == 'absent'
        ).count()
        
        course_attendance_rate = 0
        if total_course_lectures > 0:
            course_attendance_rate = (attended_lectures / total_course_lectures) * 100

        course_performance.append({
            'code': course.code,
            'title': course.title,
            'lecturer': course.lecturer,
            'attendance_rate': course_attendance_rate,
            'lectures_attended': attended_lectures,
            'lectures_missed': missed_lectures,
            'minimum_required': 75  # Minimum required attendance percentage
        })

    # Prepare stats dictionary
    stats = {
        'total_courses': len(courses),
        'courses_good': courses_good,
        'courses_at_risk': courses_at_risk,
        'total_lectures_attended': total_lectures_attended,
        'attendance_streak': attendance_streak,
        'total_lectures': total_lectures,
        'lectures_completed': lectures_completed,
        'attendance_rate': attendance_rate,
        'attendance_trend': attendance_trend
    }

    return render_template('student/dashboard.html',
                         stats=stats,
                         courses=course_performance,
                         today_lectures=today_lectures,
                         upcoming_week=upcoming_week,
                         now=current_time)

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
