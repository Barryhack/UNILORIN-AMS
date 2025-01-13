from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.attendance import Attendance
from app.models.activity_log import ActivityLog
from app.extensions import db
from app.utils.decorators import lecturer_required
from datetime import datetime, time, timedelta
from sqlalchemy import func, and_

lecturer_bp = Blueprint('lecturer', __name__)

@lecturer_bp.before_request
@login_required
@lecturer_required
def before_request():
    """Protect all lecturer routes."""
    pass

@lecturer_bp.route('/')
@lecturer_bp.route('/dashboard')
def dashboard():
    """Render the lecturer dashboard."""
    # Get lecturer's courses
    courses = Course.query.join(Lecture).filter(
        Lecture.lecturer_id == current_user.id
    ).distinct().all()

    # Get today's lectures
    today = datetime.now().date()
    today_lectures = Lecture.query.filter(
        Lecture.lecturer_id == current_user.id,
        func.date(Lecture.date) == today
    ).order_by(Lecture.start_time).all()

    # Calculate average attendance
    total_attendance = 0
    total_lectures = 0
    for course in courses:
        course_lectures = course.lectures.filter(
            Lecture.lecturer_id == current_user.id
        ).all()
        for lecture in course_lectures:
            total_attendance += lecture.attendance_count
            total_lectures += 1
    
    avg_attendance = (total_attendance / (total_lectures * len(courses))) * 100 if total_lectures > 0 and courses else 0

    # Get total students across all courses
    total_students = User.query.join(
        Course.enrolled_students
    ).filter(
        User.role == 'student',
        Course.id.in_([c.id for c in courses])
    ).distinct().count()

    # Get recent activities
    recent_activities = ActivityLog.query.filter(
        ActivityLog.user_id == current_user.id
    ).order_by(ActivityLog.created_at.desc()).limit(5).all()

    return render_template('lecturer/dashboard_new.html',
                         courses=courses,
                         today_lectures=today_lectures,
                         avg_attendance=avg_attendance,
                         total_students=total_students,
                         recent_activities=recent_activities)

@lecturer_bp.route('/check_upcoming_lectures')
def check_upcoming_lectures():
    """Check for upcoming lectures in the next hour."""
    now = datetime.now()
    one_hour_later = now + timedelta(hours=1)
    
    upcoming_lectures = Lecture.query.filter(
        Lecture.lecturer_id == current_user.id,
        Lecture.date == now.date(),
        Lecture.start_time > now.time(),
        Lecture.start_time <= one_hour_later.time()
    ).all()
    
    lecture_data = []
    for lecture in upcoming_lectures:
        lecture_start = datetime.combine(now.date(), lecture.start_time)
        minutes_until = int((lecture_start - now).total_seconds() / 60)
        
        lecture_data.append({
            'course_code': lecture.course.code,
            'course_title': lecture.course.title,
            'start_time': lecture.start_time.strftime('%H:%M'),
            'minutes_until': minutes_until
        })
    
    return jsonify({'upcoming_lectures': lecture_data})

@lecturer_bp.route('/view_courses')
def view_courses():
    """View all courses taught by the lecturer."""
    courses = Course.query.join(Lecture).filter(
        Lecture.lecturer_id == current_user.id
    ).distinct().all()
    return render_template('lecturer/courses_new.html', courses=courses)

@lecturer_bp.route('/course/<int:course_id>')
def view_course(course_id):
    """View details of a specific course."""
    course = Course.query.get_or_404(course_id)
    
    # Ensure lecturer has access to this course
    if not course.lectures.filter_by(lecturer_id=current_user.id).first():
        flash('You do not have access to this course.', 'error')
        return redirect(url_for('lecturer.view_courses'))
    
    # Get lectures and students
    lectures = course.lectures.filter_by(lecturer_id=current_user.id).all()
    students = User.query.join(
        Course.enrolled_students
    ).filter(
        User.role == 'student',
        Course.id == course_id
    ).all()
    
    # Get upcoming lectures
    now = datetime.now()
    upcoming_lectures = course.lectures.filter(
        Lecture.lecturer_id == current_user.id,
        Lecture.date >= now.date()
    ).order_by(Lecture.date, Lecture.start_time).all()
    
    # Calculate attendance statistics for each student
    attendance_stats = {}
    for student in students:
        attended = Attendance.query.join(Lecture).filter(
            Attendance.student_id == student.id,
            Lecture.course_id == course_id,
            Lecture.lecturer_id == current_user.id,
            Attendance.status == 'present'
        ).count()
        
        total_lectures = len(lectures)
        attendance_rate = (attended / total_lectures * 100) if total_lectures > 0 else 0
        attendance_stats[student.id] = {
            'attended': attended,
            'total': total_lectures,
            'rate': attendance_rate
        }
    
    # Calculate average attendance for the course
    total_attendance = sum(stat['rate'] for stat in attendance_stats.values())
    avg_attendance = total_attendance / len(attendance_stats) if attendance_stats else 0
    
    return render_template('lecturer/course_details_new.html',
                         course=course,
                         lectures=lectures,
                         upcoming_lectures=upcoming_lectures,
                         students=students,
                         attendance_stats=attendance_stats,
                         avg_attendance=avg_attendance)

@lecturer_bp.route('/lecture/<int:lecture_id>/attendance', methods=['GET', 'POST'])
def take_attendance(lecture_id):
    """Take attendance for a specific lecture."""
    lecture = Lecture.query.get_or_404(lecture_id)
    
    # Ensure lecturer has access to this lecture
    if lecture.lecturer_id != current_user.id:
        flash('You do not have access to this lecture.', 'error')
        return redirect(url_for('lecturer.dashboard'))
    
    if request.method == 'POST':
        try:
            # Clear existing attendance records
            Attendance.query.filter_by(lecture_id=lecture_id).delete()
            
            # Get list of present students
            present_students = request.form.getlist('present_students')
            
            # Create new attendance records
            for student_id in present_students:
                attendance = Attendance(
                    student_id=student_id,
                    lecture_id=lecture_id,
                    course_id=lecture.course_id,
                    status='present'
                )
                db.session.add(attendance)
            
            db.session.commit()
            
            # Log activity
            ActivityLog.log_activity(
                user_id=current_user.id,
                action=f"Took attendance for {lecture.course.code} lecture on {lecture.date}",
                category="attendance"
            )
            
            flash('Attendance recorded successfully.', 'success')
            return redirect(url_for('lecturer.view_course', course_id=lecture.course_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording attendance: {str(e)}', 'error')
    
    students = User.query.join(
        Course.enrolled_students
    ).filter(
        User.role == 'student',
        Course.id == lecture.course_id
    ).all()
    existing_attendance = {a.student_id: a.status for a in lecture.attendances}
    
    return render_template('lecturer/attendance.html',
                         lecture=lecture,
                         students=students,
                         existing_attendance=existing_attendance)

@lecturer_bp.route('/lecture/<int:lecture_id>/view-attendance')
def view_attendance(lecture_id):
    """View attendance for a specific lecture."""
    lecture = Lecture.query.get_or_404(lecture_id)
    
    # Ensure lecturer has access to this lecture
    if lecture.lecturer_id != current_user.id:
        flash('You do not have access to this lecture.', 'error')
        return redirect(url_for('lecturer.dashboard'))
    
    attendances = lecture.attendances.all()
    students = User.query.join(
        Course.enrolled_students
    ).filter(
        User.role == 'student',
        Course.id == lecture.course_id
    ).all()
    
    # Create a dictionary of attendance status
    attendance_dict = {a.student_id: a.status for a in attendances}
    
    return render_template('lecturer/view_attendance.html',
                         lecture=lecture,
                         students=students,
                         attendance_dict=attendance_dict)

@lecturer_bp.route('/course/<int:course_id>/attendance-report')
def course_attendance_report(course_id):
    """Generate attendance report for a course."""
    course = Course.query.get_or_404(course_id)
    
    # Ensure lecturer has access to this course
    if not course.lectures.filter_by(lecturer_id=current_user.id).first():
        flash('You do not have access to this course.', 'error')
        return redirect(url_for('lecturer.view_courses'))
    
    lectures = course.lectures.filter_by(lecturer_id=current_user.id).all()
    students = User.query.join(
        Course.enrolled_students
    ).filter(
        User.role == 'student',
        Course.id == course_id
    ).all()
    
    # Calculate attendance statistics for each student
    attendance_data = {}
    for student in students:
        student_attendance = []
        for lecture in lectures:
            attendance = Attendance.query.filter_by(
                student_id=student.id,
                lecture_id=lecture.id
            ).first()
            student_attendance.append({
                'date': lecture.date,
                'status': attendance.status if attendance else 'absent'
            })
        
        # Calculate attendance rate
        attended = len([a for a in student_attendance if a['status'] == 'present'])
        attendance_rate = (attended / len(lectures) * 100) if lectures else 0
        
        attendance_data[student.id] = {
            'attendance': student_attendance,
            'rate': attendance_rate
        }
    
    return render_template('lecturer/course_attendance.html',
                         course=course,
                         lectures=lectures,
                         students=students,
                         attendance_data=attendance_data)
