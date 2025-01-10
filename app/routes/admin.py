from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
import psutil
from app.models import User, Attendance, Lecture, LoginLog, ActivityLog
from app.utils.decorators import roles_required
from sqlalchemy import func
import json
import serial
import serial.tools.list_ports

admin_bp = Blueprint('admin', __name__)

# Global variables for hardware state
hardware_state = {
    'controller_connected': False,
    'fingerprint_ready': False,
    'rfid_ready': False,
    'serial_port': None
}

@admin_bp.route('/dashboard')
@login_required
@roles_required('admin')
def dashboard():
    today = datetime.utcnow().date()
    
    # Get statistics for dashboard
    stats = {
        'total_users': User.query.count(),
        'total_students': User.query.filter_by(role='student').count(),
        'total_lecturers': User.query.filter_by(role='lecturer').count(),
        'today_attendance': Attendance.query.filter(
            func.date(Attendance.timestamp) == today
        ).count(),
        'present_count': Attendance.query.filter(
            func.date(Attendance.timestamp) == today,
            Attendance.status == 'present'
        ).count(),
        'absent_count': Attendance.query.filter(
            func.date(Attendance.timestamp) == today,
            Attendance.status == 'absent'
        ).count(),
        'total_registrations': User.query.filter(
            (User.fingerprint_data.isnot(None)) | 
            (User.rfid_data.isnot(None))
        ).count(),
        'fingerprint_count': User.query.filter(
            User.fingerprint_data.isnot(None)
        ).count()
    }
    
    # Get recent activity logs
    recent_activities = ActivityLog.query.order_by(
        ActivityLog.timestamp.desc()
    ).limit(10).all()
    
    # Get recent login logs
    recent_logins = LoginLog.query.order_by(
        LoginLog.timestamp.desc()
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_activities=recent_activities,
                         recent_logins=recent_logins,
                         datetime=datetime)

@admin_bp.route('/system-info')
@login_required
@roles_required('admin')
def system_info():
    """Get system information for monitoring."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return jsonify({
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'disk_percent': disk.percent,
        'hardware_state': hardware_state
    })

@admin_bp.route('/users')
@login_required
@roles_required('admin')
def users():
    """List all users."""
    users_list = User.query.all()
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def edit_user(user_id):
    """Edit a user."""
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        data = request.get_json()
        user.email = data.get('email', user.email)
        user.role = data.get('role', user.role)
        user.is_active = data.get('is_active', user.is_active)
        user.save()
        return jsonify({'message': 'User updated successfully'})
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/user/<string:user_id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'You cannot delete your own account'})
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    ActivityLog.log_activity(
        current_user.id,
        'delete_user',
        f'Deleted user {username}',
        'user',
        user_id
    )
    
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@admin_bp.route('/departments')
@login_required
@roles_required('admin')
def departments():
    departments = Department.query.all()
    faculties = Faculty.query.all()
    return render_template('admin/departments.html', departments=departments, faculties=faculties, datetime=datetime)

@admin_bp.route('/department/create', methods=['POST'])
@login_required
@roles_required('admin')
def create_department():
    name = request.form.get('name')
    code = request.form.get('code')
    faculty_id = request.form.get('faculty_id')
    
    if Department.query.filter_by(code=code).first():
        return jsonify({'success': False, 'error': 'Department code already exists'})
    
    department = Department(
        name=name,
        code=code,
        faculty_id=faculty_id
    )
    
    db.session.add(department)
    db.session.commit()
    
    ActivityLog.log_activity(
        current_user.id,
        'create_department',
        f'Created new department {name}',
        'department',
        department.id
    )
    
    return jsonify({'success': True, 'message': 'Department created successfully'})

@admin_bp.route('/department/<int:dept_id>/edit', methods=['POST'])
@login_required
@roles_required('admin')
def edit_department(dept_id):
    department = Department.query.get_or_404(dept_id)
    
    department.name = request.form.get('name')
    department.code = request.form.get('code')
    department.faculty_id = request.form.get('faculty_id')
    
    db.session.commit()
    
    ActivityLog.log_activity(
        current_user.id,
        'edit_department',
        f'Updated department {department.name}',
        'department',
        department.id
    )
    
    return jsonify({'success': True, 'message': 'Department updated successfully'})

@admin_bp.route('/department/<int:dept_id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_department(dept_id):
    department = Department.query.get_or_404(dept_id)
    
    # Check if department has any courses
    if department.courses:
        return jsonify({'success': False, 'error': 'Cannot delete department with associated courses'})
    
    name = department.name
    db.session.delete(department)
    db.session.commit()
    
    ActivityLog.log_activity(
        current_user.id,
        'delete_department',
        f'Deleted department {name}',
        'department',
        dept_id
    )
    
    return jsonify({'success': True, 'message': 'Department deleted successfully'})

@admin_bp.route('/courses')
@login_required
@roles_required('admin')
def courses():
    courses = Course.query.all()
    departments = Department.query.all()
    return render_template('admin/courses.html', courses=courses, departments=departments, datetime=datetime)

@admin_bp.route('/course/create', methods=['POST'])
@login_required
@roles_required('admin')
def create_course():
    name = request.form.get('name')
    code = request.form.get('code')
    department_id = request.form.get('department_id')
    
    if Course.query.filter_by(code=code).first():
        return jsonify({'success': False, 'error': 'Course code already exists'})
    
    course = Course(
        name=name,
        code=code,
        department_id=department_id
    )
    
    db.session.add(course)
    db.session.commit()
    
    ActivityLog.log_activity(
        current_user.id,
        'create_course',
        f'Created new course {name}',
        'course',
        course.id
    )
    
    return jsonify({'success': True, 'message': 'Course created successfully'})

@admin_bp.route('/course/<int:course_id>/edit', methods=['POST'])
@login_required
@roles_required('admin')
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    course.name = request.form.get('name')
    course.code = request.form.get('code')
    course.department_id = request.form.get('department_id')
    
    db.session.commit()
    
    ActivityLog.log_activity(
        current_user.id,
        'edit_course',
        f'Updated course {course.name}',
        'course',
        course.id
    )
    
    return jsonify({'success': True, 'message': 'Course updated successfully'})

@admin_bp.route('/course/<int:course_id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if course has any lectures
    if course.lectures:
        return jsonify({'success': False, 'error': 'Cannot delete course with associated lectures'})
    
    name = course.name
    db.session.delete(course)
    db.session.commit()
    
    ActivityLog.log_activity(
        current_user.id,
        'delete_course',
        f'Deleted course {name}',
        'course',
        course_id
    )
    
    return jsonify({'success': True, 'message': 'Course deleted successfully'})

@admin_bp.route('/activity-logs')
@login_required
@roles_required('admin')
def activity_logs():
    page = request.args.get('page', 1, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False)
    return render_template('admin/activity_logs.html', logs=logs, datetime=datetime)

@admin_bp.route('/login-logs')
@login_required
@roles_required('admin')
def login_logs():
    page = request.args.get('page', 1, type=int)
    logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False)
    return render_template('admin/login_logs.html', logs=logs, datetime=datetime)

@admin_bp.route('/statistics')
@login_required
@roles_required('admin')
def statistics():
    # User statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    student_count = User.query.filter_by(role='student').count()
    lecturer_count = User.query.filter_by(role='lecturer').count()
    
    # Course statistics
    total_courses = Course.query.count()
    total_lectures = Lecture.query.count()
    total_departments = Department.query.count()
    
    # Attendance statistics
    total_attendance = Attendance.query.count()
    today_attendance = Attendance.query.join(Lecture).filter(
        func.date(Lecture.date) == datetime.utcnow().date()
    ).count()
    
    # Recent activities
    recent_activities = ActivityLog.query.order_by(
        ActivityLog.timestamp.desc()
    ).limit(10).all()
    
    return render_template('admin/statistics.html',
                         total_users=total_users,
                         active_users=active_users,
                         student_count=student_count,
                         lecturer_count=lecturer_count,
                         total_courses=total_courses,
                         total_lectures=total_lectures,
                         total_departments=total_departments,
                         total_attendance=total_attendance,
                         today_attendance=today_attendance,
                         recent_activities=recent_activities,
                         datetime=datetime)

@admin_bp.route('/attendance')
@login_required
@roles_required('admin')
def attendance():
    """View and manage attendance records"""
    attendance_records = Attendance.query.order_by(Attendance.marked_at.desc()).all()
    return render_template('admin/attendance.html', attendance_records=attendance_records)

@admin_bp.route('/reports')
@login_required
@roles_required('admin')
def reports():
    """Generate and view reports"""
    return render_template('admin/reports.html')

@admin_bp.route('/settings')
@login_required
@roles_required('admin')
def settings():
    """View and modify system settings"""
    return render_template('admin/settings.html')
