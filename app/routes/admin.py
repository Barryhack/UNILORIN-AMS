"""Admin routes."""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app, jsonify, send_file
)
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from sqlalchemy import func, text, desc
from app.models.course import Course
from app.models.department import Department
from app.models.user import User
from app.models.lecture import Lecture
from app.models.course_student import CourseStudent
from app.models.attendance import Attendance
from app.models.activity_log import ActivityLog
from app.models.login_log import LoginLog
from app.forms import (
    UserForm, CourseForm, DepartmentForm, AttendanceForm,
    SettingsForm
)
from app.utils import admin_required, roles_required
from app.extensions import db
from app.hardware.controller import init_hardware, get_hardware_controller
import logging
import traceback

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def get_dashboard_statistics():
    """Get statistics for the admin dashboard."""
    try:
        # Get total users
        total_users = User.query.count()
        
        # Get total courses
        total_courses = Course.query.count()
        
        # Get total departments
        total_departments = Department.query.count()
        
        # Get today's attendance
        today = datetime.now().date()
        today_attendance = Attendance.query.filter(
            func.date(Attendance.timestamp) == today
        ).count()
        
        # Get attendance data for the last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        attendance_data = db.session.query(
            func.date(Attendance.timestamp).label('date'),
            func.count(Attendance.id).label('count')
        ).filter(
            Attendance.timestamp >= seven_days_ago
        ).group_by(
            func.date(Attendance.timestamp)
        ).order_by(
            func.date(Attendance.timestamp)
        ).all()
        
        attendance_labels = [row.date.strftime('%Y-%m-%d') for row in attendance_data]
        attendance_counts = [row.count for row in attendance_data]
        
        # Get department statistics
        department_stats = db.session.query(
            Department.name,
            func.count(User.id).label('user_count')
        ).join(
            User, Department.id == User.department_id
        ).group_by(
            Department.name
        ).all()
        
        department_labels = [dept.name for dept in department_stats]
        department_counts = [dept.user_count for dept in department_stats]
        
        return {
            'total_users': total_users,
            'total_courses': total_courses,
            'total_departments': total_departments,
            'today_attendance': today_attendance,
            'attendance_labels': attendance_labels,
            'attendance_data': attendance_counts,
            'department_labels': department_labels,
            'department_data': department_counts
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            'total_users': 0,
            'total_courses': 0,
            'total_departments': 0,
            'today_attendance': 0,
            'attendance_labels': [],
            'attendance_data': [],
            'department_labels': [],
            'department_data': []
        }

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard view."""
    try:
        # Clear template cache
        current_app.jinja_env.cache = {}
        
        # Get current time
        now = datetime.now()
        
        # Get statistics
        try:
            stats = get_dashboard_statistics()
        except Exception as e:
            logger.error(f"Error getting dashboard statistics: {e}")
            stats = {
                'total_users': 0,
                'total_courses': 0,
                'total_departments': 0,
                'today_attendance': 0,
                'attendance_data': [],
                'department_labels': [],
                'department_data': []
            }
            
        # Get recent activities
        try:
            recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(5).all()
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            recent_activities = []
            
        # Get recent registrations
        try:
            recent_registrations = User.query.order_by(User.created_at.desc()).limit(5).all()
        except Exception as e:
            logger.error(f"Error getting recent registrations: {e}")
            recent_registrations = []

        # Get hardware status
        try:
            controller = get_hardware_controller()
            if controller:
                hardware_status = controller.get_status()
            else:
                hardware_status = {'status': 'disconnected', 'message': 'Hardware controller not initialized'}
        except Exception as e:
            logger.error(f"Error getting hardware status: {e}")
            hardware_status = {'status': 'error', 'message': str(e)}

        return render_template('admin/dashboard.html',
                            now=now,
                            stats=stats,
                            hardware_status=hardware_status,
                            recent_activities=recent_activities,
                            recent_registrations=recent_registrations)
    except Exception as e:
        logger.error(f"Error in dashboard route: {e}")
        flash('Error loading dashboard. Please try again.', 'error')
        return render_template('admin/dashboard.html',
                            now=datetime.now(),
                            stats={
                                'total_users': 0,
                                'total_courses': 0,
                                'total_departments': 0,
                                'today_attendance': 0,
                                'attendance_data': [],
                                'department_labels': [],
                                'department_data': []
                            },
                            hardware_status={'status': 'error', 'message': 'Error loading hardware status'},
                            recent_activities=[],
                            recent_registrations=[])

@admin_bp.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register_user():
    """Register a new user."""
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')
            department_id = request.form.get('department_id')
            full_name = request.form.get('full_name')

            # Validate unique username and email
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return redirect(url_for('admin.register_user'))

            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'error')
                return redirect(url_for('admin.register_user'))

            # Create new user
            user = User(
                username=username,
                email=email,
                role=role,
                department_id=department_id,
                full_name=full_name
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()

            # Log activity
            ActivityLog.log_activity(
                current_user.id,
                'register_user',
                f'Registered new user: {username}',
                'user',
                user.id
            )

            flash('User registered successfully', 'success')
            return redirect(url_for('admin.manage_users'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {e}")
            flash('An error occurred while registering user', 'error')
            return redirect(url_for('admin.register_user'))

    # GET request - show registration form
    departments = Department.query.all()
    return render_template('admin/register_user.html', departments=departments)

@admin_bp.route('/hardware')
@login_required
@admin_required
def hardware():
    """Hardware management view."""
    # Get available serial ports
    ports = [port.device for port in serial.tools.list_ports.comports()]
    
    # Get hardware status
    status = {
        'controller': False,
        'fingerprint': False,
        'rfid': False,
        'current_port': None,
        'available_ports': ports
    }
    
    if hardware_controller is not None:
        try:
            status.update({
                'controller': hardware_controller.is_connected(),
                'fingerprint': hardware_controller.fingerprint_status(),
                'rfid': hardware_controller.rfid_status(),
                'current_port': hardware_controller.get_port(),
            })
        except Exception as hw_error:
            logger.error(f"Hardware status error: {hw_error}")
            status['error'] = 'Hardware communication error'

    return render_template('admin/hardware.html', status=status)

@admin_bp.route('/hardware/connect', methods=['POST'])
@login_required
@admin_required
def connect_hardware():
    """Connect to hardware device."""
    try:
        controller = get_hardware_controller()
        if controller:
            if controller.connect():
                flash('Successfully connected to hardware device.', 'success')
                return jsonify({'status': 'success', 'message': 'Connected successfully'})
            return jsonify({'status': 'error', 'message': 'Failed to connect to hardware'})
        return jsonify({'status': 'error', 'message': 'Hardware controller not initialized'})
    except Exception as e:
        logger.error(f"Error connecting to hardware: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@admin_bp.route('/hardware/disconnect', methods=['POST'])
@login_required
@admin_required
def disconnect_hardware():
    """Disconnect from hardware device."""
    try:
        controller = get_hardware_controller()
        if controller:
            controller.disconnect()
            flash('Successfully disconnected from hardware device.', 'success')
            return jsonify({'status': 'success', 'message': 'Disconnected successfully'})
        return jsonify({'status': 'error', 'message': 'Hardware controller not initialized'})
    except Exception as e:
        logger.error(f"Error disconnecting hardware: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@admin_bp.route('/hardware/status')
@login_required
@admin_required
def hardware_status():
    """Get hardware status."""
    try:
        controller = get_hardware_controller()
        if controller:
            status = controller.get_status()
            return jsonify(status)
        return jsonify({'error': 'Hardware controller not initialized'})
    except Exception as e:
        logger.error(f"Error getting hardware status: {e}")
        return jsonify({'error': str(e)})

@admin_bp.route('/api/hardware/status')
@login_required
@admin_required
def api_hardware_status():
    """Get hardware status."""
    try:
        controller = get_hardware_controller()
        if not hasattr(controller, 'is_connected'):
            controller.is_connected = False
        return jsonify({
            'status': 'connected' if controller.is_connected else 'disconnected',
            'device': controller.device if hasattr(controller, 'device') else None,
            'error': None
        })
    except Exception as e:
        logger.error(f"Error getting hardware status: {e}")
        return jsonify({
            'status': 'error',
            'device': None,
            'error': str(e)
        })

@admin_bp.route('/api/users/register', methods=['POST'])
@login_required
@admin_required
def register_user_api():
    """Register a new user with hardware verification."""
    try:
        hardware = get_hardware_controller()
        
        # Get hardware registration data
        success, reg_data, message = hardware.register_user()
        if not success:
            return jsonify({'success': False, 'message': message}), 400
        
        # Get form data
        form_data = request.form
        
        # Create new user
        user = User(
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            email=form_data['email'],
            role=form_data['role'],
            department_id=form_data['department_id'],
            fingerprint_template=reg_data['fingerprint_template'],
            rfid_card_id=reg_data['rfid_card_id']
        )
        
        # Generate default password
        default_password = f"{user.first_name.lower()}{user.last_name.lower()}123"
        user.set_password(default_password)
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Log activity
        log_activity(
            user_id=current_user.id,
            action=f"Registered new user: {user.first_name} {user.last_name}"
        )
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user_id': user.id
        })
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/manage-users')
@login_required
@admin_required
def manage_users():
    """Manage users view."""
    try:
        # Get users with eager loading of relationships
        users = User.query.options(
            db.joinedload(User.department),
            db.joinedload(User.enrolled_courses),
            db.joinedload(User.taught_courses)
        ).all()
        
        # Get departments for the form
        departments = Department.query.all()
        
        return render_template('admin/manage_users.html',
                             users=users,
                             departments=departments)
    except SQLAlchemyError as e:
        logger.error(f"Database error in manage_users: {str(e)}\n{traceback.format_exc()}")
        flash("Error loading users. Please try again later.", "error")
        return render_template('admin/manage_users.html',
                             users=[],
                             departments=[],
                             error="Database error occurred.")
    except Exception as e:
        logger.error(f"Unexpected error in manage_users: {str(e)}\n{traceback.format_exc()}")
        flash("An unexpected error occurred.", "error")
        return render_template('admin/manage_users.html',
                             users=[],
                             departments=[],
                             error="An unexpected error occurred.")

@admin_bp.route('/activity-logs')
@login_required
@admin_required
def activity_logs():
    """View activity logs."""
    try:
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
        return render_template('admin/activity_logs.html', logs=logs)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in activity_logs: {str(e)}")
        flash("Error loading activity logs. Please try again later.", "error")
        return render_template('admin/activity_logs.html', logs=[])

@admin_bp.route('/system-logs')
@login_required
@admin_required
def system_logs():
    """View system logs."""
    try:
        # Get the last 100 lines of the application log
        log_file = current_app.config.get('LOG_FILE', 'app.log')
        with open(log_file, 'r') as f:
            logs = f.readlines()[-100:]
        return render_template('admin/system_logs.html', logs=logs)
    except Exception as e:
        current_app.logger.error(f"Error reading system logs: {str(e)}")
        flash("Error loading system logs. Please try again later.", "error")
        return render_template('admin/system_logs.html', logs=[])

@admin_bp.route('/login-logs')
@login_required
@admin_required
def login_logs():
    """View login logs."""
    try:
        logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(100).all()
        return render_template('admin/login_logs.html', logs=logs)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in login_logs: {str(e)}")
        flash("Error loading login logs. Please try again later.", "error")
        return render_template('admin/login_logs.html', logs=[])

@admin_bp.route('/manage-courses')
@login_required
@admin_required
def manage_courses():
    """Manage courses view."""
    try:
        # Get courses with eager loading of relationships
        courses = Course.query.options(
            db.joinedload(Course.department),
            db.joinedload(Course.lecturer),
            db.joinedload(Course.enrolled_students),
            db.joinedload(Course.lectures)
        ).all()
        
        # Get departments and lecturers for the form
        departments = Department.query.all()
        lecturers = User.query.filter(User.role.in_(['lecturer', 'admin'])).all()
        
        return render_template('admin/manage_courses.html',
                             courses=courses,
                             departments=departments,
                             lecturers=lecturers)
    except SQLAlchemyError as e:
        logger.error(f"Database error in manage_courses: {str(e)}\n{traceback.format_exc()}")
        flash("Error loading courses. Please try again later.", "error")
        return render_template('admin/manage_courses.html',
                             courses=[],
                             departments=[],
                             lecturers=[],
                             error="Database error occurred.")
    except Exception as e:
        logger.error(f"Unexpected error in manage_courses: {str(e)}\n{traceback.format_exc()}")
        flash("An unexpected error occurred.", "error")
        return render_template('admin/manage_courses.html',
                             courses=[],
                             departments=[],
                             lecturers=[],
                             error="An unexpected error occurred.")

@admin_bp.route('/manage-departments')
@login_required
@admin_required
def manage_departments():
    """Manage departments view."""
    try:
        # Get departments with eager loading of relationships
        departments = Department.query.options(
            db.joinedload(Department.department_users),
            db.joinedload(Department.courses)
        ).all()
        
        return render_template('admin/manage_departments.html',
                             departments=departments)
    except SQLAlchemyError as e:
        logger.error(f"Database error in manage_departments: {str(e)}\n{traceback.format_exc()}")
        flash("Error loading departments. Please try again later.", "error")
        return render_template('admin/manage_departments.html',
                             departments=[],
                             error="Database error occurred.")
    except Exception as e:
        logger.error(f"Unexpected error in manage_departments: {str(e)}\n{traceback.format_exc()}")
        flash("An unexpected error occurred.", "error")
        return render_template('admin/manage_departments.html',
                             departments=[],
                             error="An unexpected error occurred.")

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """View system reports."""
    return render_template('admin/reports.html')

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users."""
    users_list = User.query.all()
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
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
@admin_required
def delete_user(user_id):
    """Delete user from system."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent self-deletion
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'You cannot delete your own account'})
        
        # Store user info for logging
        username = user.username
        
        # Delete user's fingerprint and RFID data if hardware is connected
        if hardware_controller is not None and hardware_controller.is_connected():
            hardware_controller.delete_user_data(user_id)
        
        # Delete user from database
        db.session.delete(user)
        db.session.commit()
        
        # Log the activity
        ActivityLog.log_activity(
            current_user.id,
            'delete_user',
            f'Deleted user {username}',
            'user',
            user_id
        )
        
        flash(f'User {username} has been deleted successfully.', 'success')
        return jsonify({'success': True, 'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {e}")
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/departments')
@login_required
@admin_required
def departments():
    departments = Department.query.all()
    faculties = Faculty.query.all()
    return render_template('admin/departments.html', departments=departments, faculties=faculties, datetime=datetime)

@admin_bp.route('/department/create', methods=['POST'])
@login_required
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def courses():
    courses = Course.query.all()
    departments = Department.query.all()
    return render_template('admin/courses.html', courses=courses, departments=departments, datetime=datetime)

@admin_bp.route('/course/create', methods=['POST'])
@login_required
@admin_required
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
@admin_required
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
@admin_required
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

@admin_bp.route('/statistics')
@login_required
@admin_required
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
@admin_required
def attendance():
    """View and manage attendance records"""
    attendance_records = Attendance.query.order_by(Attendance.marked_at.desc()).all()
    return render_template('admin/attendance.html', attendance_records=attendance_records)

@admin_bp.route('/course/enroll', methods=['POST'])
@login_required
@admin_required
def enroll_in_course():
    """Enroll user in course."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        course_id = data.get('course_id')
        
        user = User.query.get(user_id)
        course = Course.query.get(course_id)
        
        if not user or not course:
            return jsonify({
                'success': False,
                'message': 'User or course not found'
            })
            
        if course not in user.courses:
            user.courses.append(course)
            db.session.commit()
            
        return jsonify({
            'success': True,
            'message': 'User enrolled successfully'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error enrolling user: {e}")
        return jsonify({
            'success': False,
            'message': f'Error enrolling user: {str(e)}'
        })

@admin_bp.route('/course/unenroll', methods=['POST'])
@login_required
@admin_required
def unenroll_from_course():
    """Remove user from course."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        course_id = data.get('course_id')
        
        user = User.query.get(user_id)
        course = Course.query.get(course_id)
        
        if not user or not course:
            return jsonify({
                'success': False,
                'message': 'User or course not found'
            })
            
        if course in user.courses:
            user.courses.remove(course)
            db.session.commit()
            
        return jsonify({
            'success': True,
            'message': 'User unenrolled successfully'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error unenrolling user: {e}")
        return jsonify({
            'success': False,
            'message': f'Error unenrolling user: {str(e)}'
        })

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Admin settings view."""
    form = SettingsForm()
    if form.validate_on_submit():
        try:
            # Save settings
            current_app.config['SYSTEM_NAME'] = form.system_name.data
            current_app.config['ADMIN_EMAIL'] = form.admin_email.data
            flash('Settings updated successfully', 'success')
            return redirect(url_for('admin.settings'))
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            flash('Error updating settings', 'error')
    
    # Pre-fill form with current settings
    form.system_name.data = current_app.config.get('SYSTEM_NAME', 'AMS')
    form.admin_email.data = current_app.config.get('ADMIN_EMAIL', '')
    
    return render_template('admin/settings.html', form=form)
