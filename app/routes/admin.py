from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, current_app, flash, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app.models.user import User
from app.models.course import Course
from app.models.department import Department
from app.models.attendance import Attendance
from app.models.activity_log import ActivityLog
from app.models.hardware import HardwareStatus
from app.auth.decorators import admin_required, roles_required
from app.extensions import db
from app.utils.hardware import HardwareController
import serial.tools.list_ports
import json

admin_bp = Blueprint('admin', __name__)

# Initialize hardware controller
hardware_controller = HardwareController()

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
        # Get current time
        now = datetime.now()
        
        # Get basic statistics
        stats = {
            'total_students': User.query.filter_by(role='student').count(),
            'total_lecturers': User.query.filter_by(role='lecturer').count(),
            'total_departments': Department.query.count(),
            'total_courses': Course.query.count(),
            'today_attendance': Attendance.query.filter(
                Attendance.timestamp >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count()
        }
        
        # Get department statistics with lecturer count
        departments = []
        for dept in Department.query.all():
            student_count = User.query.filter_by(department_id=dept.id, role='student').count()
            lecturer_count = User.query.filter_by(department_id=dept.id, role='lecturer').count()
            departments.append({
                'name': dept.name,
                'student_count': student_count,
                'lecturer_count': lecturer_count
            })

        # Get hardware status
        hardware_status = {
            'controller': hardware_controller.is_connected(),
            'fingerprint': hardware_controller.fingerprint_status(),
            'rfid': hardware_controller.rfid_status(),
            'last_updated': datetime.now().strftime('%H:%M:%S')
        }

        # Get recent activities
        recent_activities = ActivityLog.query.order_by(
            ActivityLog.timestamp.desc()
        ).limit(5).all()

        # Get recent registrations
        recent_registrations = User.query.order_by(
            User.created_at.desc()
        ).limit(5).all()

        return render_template('admin/dashboard.html',
                            now=now,
                            stats=stats,
                            departments=departments,
                            hardware_status=hardware_status,
                            recent_activities=recent_activities,
                            recent_registrations=recent_registrations)

    except Exception as e:
        current_app.logger.error(f"Error in dashboard route: {e}")
        flash('An error occurred while loading the dashboard. Please try again later.', 'error')
        return render_template('error/500.html'), 500

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
            current_app.logger.error(f"Error registering user: {e}")
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
        'controller': hardware_controller.is_connected(),
        'fingerprint': hardware_controller.fingerprint_status(),
        'rfid': hardware_controller.rfid_status(),
        'current_port': hardware_controller.get_port(),
        'available_ports': ports
    }
    
    return render_template('admin/hardware.html', status=status)

@admin_bp.route('/api/hardware/connect', methods=['POST'])
@login_required
@admin_required
def connect_hardware():
    """Connect to hardware devices."""
    try:
        port = request.form.get('port')
        if hardware_controller.connect(port):
            return jsonify({
                'success': True,
                'message': 'Hardware connected successfully'
            })
        return jsonify({
            'success': False,
            'message': 'Failed to connect to hardware'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@admin_bp.route('/api/hardware/disconnect', methods=['POST'])
@login_required
@admin_required
def disconnect_hardware():
    """Disconnect hardware devices."""
    try:
        hardware_controller.disconnect()
        return jsonify({
            'success': True,
            'message': 'Hardware disconnected successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@admin_bp.route('/api/hardware/test', methods=['POST'])
@login_required
@admin_required
def test_hardware():
    """Test hardware devices."""
    try:
        device = request.form.get('device')  # 'fingerprint' or 'rfid'
        result = hardware_controller.test_device(device)
        return jsonify({
            'success': True,
            'working': result,
            'message': f'Device test {"successful" if result else "failed"}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@admin_bp.route('/api/hardware/status')
@login_required
@admin_required
def get_hardware_status():
    """Get current hardware status."""
    try:
        status = {
            'controller': hardware_controller.is_connected(),
            'fingerprint': hardware_controller.fingerprint_status(),
            'rfid': hardware_controller.rfid_status(),
            'last_updated': datetime.now().strftime('%H:%M:%S')
        }
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@admin_bp.route('/manage-users')
@login_required
@admin_required
def manage_users():
    """Manage users view."""
    users = User.query.order_by(User.created_at.desc()).all()
    departments = Department.query.all()
    
    # Group users by role for better organization
    students = [u for u in users if u.role == 'student']
    lecturers = [u for u in users if u.role == 'lecturer']
    admins = [u for u in users if u.role == 'admin']
    
    return render_template('admin/manage_users.html',
                         users=users,
                         students=students,
                         lecturers=lecturers,
                         admins=admins,
                         departments=departments)

@admin_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Update user details."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update user fields
        user.full_name = data.get('full_name', user.full_name)
        user.email = data.get('email', user.email)
        user.department_id = data.get('department_id', user.department_id)
        user.role = data.get('role', user.role)
        user.is_active = data.get('is_active', user.is_active)
        
        db.session.commit()
        
        # Log activity
        ActivityLog.log_activity(
            current_user.id,
            'update_user',
            f'Updated user: {user.username}',
            'user',
            user.id
        )
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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

@admin_bp.route('/hardware/connect', methods=['POST'])
@login_required
@admin_required
def connect_hardware():
    """Connect to hardware device."""
    try:
        port = request.form.get('port')
        if not port:
            return jsonify({'success': False, 'message': 'Port is required'})
            
        success = hardware_controller.connect(port)
        return jsonify({'success': success, 'message': 'Connected successfully' if success else 'Connection failed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/hardware/disconnect', methods=['POST'])
@login_required
@admin_required
def disconnect_hardware():
    """Disconnect from hardware device."""
    try:
        hardware_controller.disconnect()
        return jsonify({'success': True, 'message': 'Disconnected successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/hardware/status', methods=['GET'])
@login_required
@admin_required
def get_hardware_status():
    """Get hardware status."""
    try:
        status = hardware_controller.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/register/start', methods=['POST'])
@login_required
@admin_required
def start_registration():
    """Start user registration process."""
    try:
        success, result = hardware_controller.start_registration()
        if success:
            return jsonify({
                'success': True,
                'user_id': result,
                'message': 'Registration started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Registration failed: {result}'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting registration: {str(e)}'
        })

@admin_bp.route('/register/complete', methods=['POST'])
@login_required
@admin_required
def complete_registration():
    """Complete user registration with details."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_details = {
            'full_name': data.get('full_name'),
            'matric_number': data.get('matric_number'),
            'department': data.get('department'),
            'level': data.get('level'),
            'email': data.get('email')
        }
        
        # Create new user in database
        new_user = User(
            id=user_id,
            full_name=user_details['full_name'],
            matric_number=user_details['matric_number'],
            department=user_details['department'],
            level=user_details['level'],
            email=user_details['email']
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': {
                'id': new_user.id,
                'full_name': new_user.full_name,
                'matric_number': new_user.matric_number
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error completing registration: {str(e)}'
        })

@admin_bp.route('/verify/start', methods=['POST'])
@login_required
@admin_required
def start_verification():
    """Start user verification process."""
    try:
        course_id = request.form.get('course_id')
        if not course_id:
            return jsonify({'success': False, 'message': 'Course ID is required'})
            
        success, result = hardware_controller.verify_user()
        if not success:
            return jsonify({'success': False, 'message': result})
            
        # Record attendance
        success, message = hardware_controller.record_attendance(result, course_id)
        if success:
            # Create attendance record in database
            attendance = Attendance(
                user_id=result['id'],
                course_id=course_id,
                timestamp=datetime.now()
            )
            db.session.add(attendance)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Attendance recorded successfully',
                'user': result
            })
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error during verification: {str(e)}'
        })

@admin_bp.route('/user/delete/<user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user from system."""
    try:
        # Delete from hardware first
        success, message = hardware_controller.delete_user(user_id)
        if not success:
            return jsonify({'success': False, 'message': message})
            
        # Delete from database
        user = User.query.get(user_id)
        if user:
            # Remove from all courses
            user.courses = []
            # Delete attendance records
            Attendance.query.filter_by(user_id=user_id).delete()
            # Delete user
            db.session.delete(user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'User deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'User not found'
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting user: {str(e)}'
        })

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
        return jsonify({
            'success': False,
            'message': f'Error unenrolling user: {str(e)}'
        })
