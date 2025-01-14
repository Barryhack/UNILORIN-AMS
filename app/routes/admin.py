from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, current_app, flash
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app.models.user import User
from app.models.course import Course
from app.models.department import Department
from app.models.attendance import Attendance
from app.models.activity_log import ActivityLog
from app.auth.decorators import admin_required, roles_required
from app.extensions import db

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
@admin_required
def dashboard():
    """Admin dashboard view."""
    try:
        # Get hardware status with error handling
        hardware_status = {
            'status': 'Unknown',
            'mode': 'Unknown',
            'last_update': datetime.now(),
            'fingerprint_ready': False,
            'rfid_ready': False
        }
        
        if hasattr(current_app, 'hardware_controller'):
            try:
                hardware_status = current_app.hardware_controller.get_status()
            except Exception as e:
                current_app.logger.error(f"Error getting hardware status: {e}")

        # Get basic statistics with error handling
        try:
            stats = {
                'total_users': User.query.count(),
                'total_students': User.query.filter_by(role='student').count(),
                'total_lecturers': User.query.filter_by(role='lecturer').count(),
                'total_courses': Course.query.count(),
                'total_departments': Department.query.count(),
                'today_attendance': Attendance.query.filter(
                    Attendance.timestamp >= datetime.now().replace(hour=0, minute=0, second=0)
                ).count()
            }
        except Exception as e:
            current_app.logger.error(f"Error getting basic statistics: {e}")
            stats = {
                'total_users': 0,
                'total_students': 0,
                'total_lecturers': 0,
                'total_courses': 0,
                'total_departments': 0,
                'today_attendance': 0
            }

        # Get attendance trends with error handling
        try:
            today = datetime.now().date()
            attendance_trends = []
            for i in range(7):
                date = today - timedelta(days=i)
                count = Attendance.query.filter(
                    func.date(Attendance.timestamp) == date
                ).count()
                attendance_trends.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            attendance_trends.reverse()
        except Exception as e:
            current_app.logger.error(f"Error getting attendance trends: {e}")
            attendance_trends = [{'date': today.strftime('%Y-%m-%d'), 'count': 0}]

        # Get department statistics with error handling
        try:
            dept_stats = db.session.query(
                Department.name,
                func.count(User.id).label('student_count')
            ).join(User, User.department_id == Department.id
            ).filter(User.role == 'student'
            ).group_by(Department.name
            ).all()
        except Exception as e:
            current_app.logger.error(f"Error getting department statistics: {e}")
            dept_stats = []

        # Get recent activities with error handling
        try:
            recent_activities = ActivityLog.query.order_by(
                ActivityLog.timestamp.desc()
            ).limit(10).all()
        except Exception as e:
            current_app.logger.error(f"Error getting recent activities: {e}")
            recent_activities = []

        # Get recent attendance records with error handling
        try:
            recent_attendance = db.session.query(
                Attendance, User, Course
            ).join(User, Attendance.student_id == User.id
            ).join(Course, Attendance.course_id == Course.id
            ).order_by(Attendance.timestamp.desc()
            ).limit(10).all()
        except Exception as e:
            current_app.logger.error(f"Error getting recent attendance: {e}")
            recent_attendance = []

        # Get active courses with error handling
        try:
            active_courses = db.session.query(
                Course.name,
                func.count(Attendance.id).label('attendance_count')
            ).join(Attendance, Attendance.course_id == Course.id
            ).filter(Attendance.timestamp >= datetime.now() - timedelta(hours=24)
            ).group_by(Course.name
            ).order_by(desc('attendance_count')
            ).limit(5).all()
        except Exception as e:
            current_app.logger.error(f"Error getting active courses: {e}")
            active_courses = []

        # Get system health
        system_health = {
            'database_connection': True,
            'hardware_connection': hardware_status['status'] == 'Connected',
            'fingerprint_status': hardware_status.get('fingerprint_ready', False),
            'rfid_status': hardware_status.get('rfid_ready', False),
            'last_backup': 'Not configured'
        }

        return render_template('admin/dashboard.html',
                            stats=stats,
                            attendance_trends=attendance_trends,
                            dept_stats=dept_stats,
                            recent_activities=recent_activities,
                            recent_attendance=recent_attendance,
                            active_courses=active_courses,
                            system_health=system_health,
                            hardware_status=hardware_status)

    except Exception as e:
        current_app.logger.error(f"Error in dashboard route: {e}")
        flash('An error occurred while loading the dashboard. Please try again later.', 'error')
        return render_template('error/500.html'), 500

@admin_bp.route('/api/dashboard/stats')
@login_required
@admin_required
def get_dashboard_stats():
    """Get real-time dashboard statistics."""
    try:
        stats = {
            'total_users': User.query.count(),
            'total_students': User.query.filter_by(role='student').count(),
            'total_lecturers': User.query.filter_by(role='lecturer').count(),
            'total_courses': Course.query.count(),
            'total_departments': Department.query.count(),
            'today_attendance': Attendance.query.filter(
                Attendance.timestamp >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count()
        }
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/manage-users')
@login_required
@admin_required
def manage_users():
    """Manage users view."""
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/manage-courses')
@login_required
@admin_required
def manage_courses():
    """Manage courses view."""
    courses = Course.query.all()
    departments = Department.query.all()
    return render_template('admin/manage_courses.html', 
                         courses=courses,
                         departments=departments)

@admin_bp.route('/manage-departments')
@login_required
@admin_required
def manage_departments():
    """Manage departments view."""
    departments = Department.query.all()
    return render_template('admin/manage_departments.html', departments=departments)

@admin_bp.route('/activity-logs')
@login_required
@admin_required
def activity_logs():
    """View activity logs."""
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return render_template('admin/activity_logs.html', logs=logs)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """View system reports."""
    return render_template('admin/reports.html')

@admin_bp.route('/system-logs')
@login_required
@admin_required
def system_logs():
    """View system logs."""
    activity_logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    login_logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(100).all()
    return render_template('admin/system_logs.html', 
                         activity_logs=activity_logs,
                         login_logs=login_logs)

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
        db.func.date(Lecture.date) == datetime.utcnow().date()
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

@admin_bp.route('/hardware/status')
@login_required
@admin_required
def hardware_status():
    """Get hardware status."""
    try:
        status = current_app.hardware_controller.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/hardware/connect', methods=['POST'])
@login_required
@admin_required
def hardware_connect():
    """Connect to hardware."""
    try:
        current_app.hardware_controller.connect()
        ActivityLog.create(
            user_id=current_user.id,
            action='Hardware Connection',
            details='Successfully connected to hardware'
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/hardware/disconnect', methods=['POST'])
@login_required
@admin_required
def hardware_disconnect():
    """Disconnect from hardware."""
    try:
        current_app.hardware_controller.disconnect()
        ActivityLog.create(
            user_id=current_user.id,
            action='Hardware Connection',
            details='Successfully disconnected from hardware'
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/hardware/reset', methods=['POST'])
@login_required
@admin_required
def hardware_reset():
    """Reset hardware."""
    try:
        current_app.hardware_controller.reset()
        ActivityLog.create(
            user_id=current_user.id,
            action='Hardware Reset',
            details='Successfully reset hardware'
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/hardware/test', methods=['POST'])
@login_required
@admin_required
def hardware_test():
    """Test hardware."""
    try:
        test_result = current_app.hardware_controller.test()
        ActivityLog.create(
            user_id=current_user.id,
            action='Hardware Test',
            details='Hardware test completed'
        )
        return jsonify({'success': True, 'test_result': test_result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
