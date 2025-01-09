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
from app.extensions import socketio

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
        ).count(),
        'rfid_count': User.query.filter(
            User.rfid_data.isnot(None)
        ).count()
    }
    
    # Get recent activities
    recent_activities = ActivityLog.query.order_by(
        ActivityLog.timestamp.desc()
    ).limit(5).all()
    
    activities_list = []
    for activity in recent_activities:
        icon = 'fa-user'  # default icon
        if 'login' in activity.action.lower():
            icon = 'fa-sign-in-alt'
        elif 'attendance' in activity.action.lower():
            icon = 'fa-clipboard-check'
        elif 'registration' in activity.action.lower():
            icon = 'fa-id-card'
            
        activities_list.append({
            'action': activity.action,
            'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'icon': icon
        })
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_activities=activities_list
    )

@socketio.on('connect')
def handle_connect():
    current_app.logger.info('Client connected')
    socketio.emit('status', hardware_state)

@socketio.on('disconnect')
def handle_disconnect():
    current_app.logger.info('Client disconnected')

@admin_bp.route('/hardware/connect', methods=['POST'])
@login_required
@roles_required('admin')
def connect_controller():
    try:
        if hardware_state['controller_connected']:
            return jsonify({'success': False, 'error': 'Controller already connected'})
            
        # Find available COM ports
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            return jsonify({'success': False, 'error': 'No COM ports found'})
            
        # Try to connect to the first available port
        for port in ports:
            try:
                ser = serial.Serial(port.device, 9600, timeout=1)
                hardware_state['serial_port'] = ser
                hardware_state['controller_connected'] = True
                
                # Send initialization command
                ser.write(b'INIT\n')
                response = ser.readline().decode().strip()
                
                if response == 'OK':
                    hardware_state['fingerprint_ready'] = True
                    hardware_state['rfid_ready'] = True
                    socketio.emit('status', hardware_state)
                    return jsonify({'success': True})
                else:
                    ser.close()
                    hardware_state['controller_connected'] = False
                    return jsonify({'success': False, 'error': 'Invalid response from controller'})
                    
            except Exception as e:
                continue
                
        return jsonify({'success': False, 'error': 'Could not connect to any available port'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/hardware/test', methods=['POST'])
@login_required
@roles_required('admin')
def test_hardware():
    try:
        if not hardware_state['controller_connected']:
            return jsonify({'success': False, 'error': 'Controller not connected'})
            
        ser = hardware_state['serial_port']
        
        # Send test command
        ser.write(b'TEST\n')
        response = ser.readline().decode().strip()
        
        if response == 'OK':
            socketio.emit('status', hardware_state)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Test failed'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/system-info')
@login_required
@roles_required('admin')
def system_info():
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    return jsonify({
        'status': 'Online' if cpu_percent < 80 else 'High Load',
        'cpu_percent': cpu_percent,
        'memory': {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent
        }
    })

@admin_bp.route('/users')
@login_required
@roles_required('admin')
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users, datetime=datetime)

@admin_bp.route('/user/<string:user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.role = request.form.get('role')
        user.is_active = bool(request.form.get('is_active'))
        
        if request.form.get('password'):
            user.password_hash = generate_password_hash(request.form.get('password'))
        
        db.session.commit()
        
        ActivityLog.log_activity(
            current_user.id,
            'edit_user',
            f'Updated user {user.username}',
            'user',
            user.id
        )
        
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user, datetime=datetime)

@admin_bp.route('/user/create', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('admin.create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('admin.create_user'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name')
        )
        
        db.session.add(user)
        db.session.commit()
        
        ActivityLog.log_activity(
            current_user.id,
            'create_user',
            f'Created new user {username}',
            'user',
            user.id
        )
        
        flash('User created successfully', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html', datetime=datetime)

@admin_bp.route('/user/<string:user_id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin.users'))
    
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
    
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.users'))

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
        flash('Department code already exists', 'error')
        return redirect(url_for('admin.departments'))
    
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
    
    flash('Department created successfully', 'success')
    return redirect(url_for('admin.departments'))

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
    
    flash('Department updated successfully', 'success')
    return redirect(url_for('admin.departments'))

@admin_bp.route('/department/<int:dept_id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_department(dept_id):
    department = Department.query.get_or_404(dept_id)
    
    # Check if department has any courses
    if department.courses:
        flash('Cannot delete department with associated courses', 'error')
        return redirect(url_for('admin.departments'))
    
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
    
    flash('Department deleted successfully', 'success')
    return redirect(url_for('admin.departments'))

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
        flash('Course code already exists', 'error')
        return redirect(url_for('admin.courses'))
    
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
    
    flash('Course created successfully', 'success')
    return redirect(url_for('admin.courses'))

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
    
    flash('Course updated successfully', 'success')
    return redirect(url_for('admin.courses'))

@admin_bp.route('/course/<int:course_id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if course has any lectures
    if course.lectures:
        flash('Cannot delete course with associated lectures', 'error')
        return redirect(url_for('admin.courses'))
    
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
    
    flash('Course deleted successfully', 'success')
    return redirect(url_for('admin.courses'))

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
