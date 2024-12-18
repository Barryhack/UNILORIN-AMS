from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.user import User
from app.models.department import Department
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.system_settings import SystemSettings
from app.forms.settings import SystemSettingsForm
from app import db
from sqlalchemy import or_
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get current time for the dashboard
    current_time = datetime.now()
    
    # Get statistics
    total_students = User.query.filter_by(role='student').count()
    total_lecturers = User.query.filter_by(role='lecturer').count()
    total_departments = Department.query.count()
    total_courses = Course.query.count()
    
    # Get department statistics
    department_stats = []
    departments = Department.query.all()
    for dept in departments:
        stats = {
            'name': dept.name,
            'code': dept.code,
            'student_count': User.query.filter_by(department_id=dept.id, role='student').count(),
            'lecturer_count': User.query.filter_by(department_id=dept.id, role='lecturer').count(),
            'course_count': Course.query.filter_by(department_id=dept.id).count()
        }
        department_stats.append(stats)
    
    # Get recent users (last 5 registered)
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         current_time=current_time,
                         total_students=total_students,
                         total_lecturers=total_lecturers,
                         total_departments=total_departments,
                         total_courses=total_courses,
                         department_stats=department_stats,
                         recent_users=recent_users)

@admin_bp.route('/manage_users')
@login_required
@admin_required
def manage_users():
    try:
        print("Debug: Starting manage_users route")  # Debug print
        page = request.args.get('page', 1, type=int)
        per_page = 10

        # Get filter parameters
        role_filter = request.args.get('role', '')
        department_filter = request.args.get('department', '')
        search_query = request.args.get('search', '')
        
        print(f"Debug: Filters - role: {role_filter}, department: {department_filter}, search: {search_query}")  # Debug print

        # Base query
        query = User.query

        # Apply filters
        if role_filter and role_filter.strip():
            query = query.filter(User.role == role_filter.strip())
        
        # Handle department filter
        try:
            if department_filter:
                department_id = int(department_filter) if department_filter.strip() else None
                if department_id is not None:
                    query = query.filter(User.department_id == department_id)
        except (ValueError, TypeError) as e:
            print(f"Debug: Error converting department_id: {str(e)}")  # Debug print
            # Don't raise the error, just skip the department filter
            pass
        
        if search_query and search_query.strip():
            search = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    User.name.ilike(search),
                    User.email.ilike(search)
                )
            )

        # Get paginated results
        print("Debug: Executing query")  # Debug print
        pagination = query.order_by(User.name).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        users = pagination.items

        # Get all departments for the filter dropdown
        departments = Department.query.order_by(Department.name).all()
        print(f"Debug: Found {len(departments)} departments")  # Debug print

        return render_template(
            'admin/manage_users.html',
            users=users,
            pagination=pagination,
            departments=departments
        )
    except Exception as e:
        print(f"Error in manage_users: {str(e)}")  # Debug print
        import traceback
        print(f"Debug: Full traceback:\n{traceback.format_exc()}")  # Debug print
        flash(f'Error loading users: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent self-deactivation
    if user == current_user:
        return jsonify({
            'success': False,
            'message': 'You cannot deactivate your own account'
        }), 400

    try:
        current_status = user.is_active
        user.is_active = not current_status
        
        # Store the status in session since we don't have a database column
        if not hasattr(user, '_is_active_dict'):
            user._is_active_dict = {}
        user._is_active_dict[user.id] = user.is_active
        
        status = 'activated' if user.is_active else 'deactivated'
        return jsonify({
            'success': True,
            'message': f'User {status} successfully',
            'is_active': user.is_active
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error toggling user status: {str(e)}'
        }), 500

@admin_bp.route('/register_user', methods=['GET', 'POST'])
@login_required
@admin_required
def register_user():
    if request.method == 'POST':
        # Handle user registration logic here
        pass
    return render_template('admin/register_user.html')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    departments = Department.query.order_by(Department.name).all()
    
    if request.method == 'POST':
        try:
            # Update basic info
            user.name = request.form.get('name')
            user.email = request.form.get('email')
            user.role = request.form.get('role')
            
            # Handle department
            department_id = request.form.get('department_id')
            user.department_id = int(department_id) if department_id and department_id.strip() else None
            
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating user: ' + str(e), 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))
    
    return render_template('admin/edit_user.html', user=user, departments=departments)

@admin_bp.route('/manage_departments')
@login_required
@admin_required
def manage_departments():
    departments = Department.query.all()
    return render_template('admin/manage_departments.html', departments=departments)

@admin_bp.route('/manage_courses')
@login_required
@admin_required
def manage_courses():
    courses = Course.query.all()
    departments = Department.query.all()
    lecturers = User.query.filter_by(role='lecturer').all()
    return render_template('admin/manage_courses.html', 
                         courses=courses,
                         departments=departments,
                         lecturers=lecturers)

@admin_bp.route('/department/<int:department_id>')
@login_required
@admin_required
def get_department(department_id):
    department = Department.query.get_or_404(department_id)
    return jsonify({
        'id': department.id,
        'code': department.code,
        'name': department.name,
        'description': department.description
    })

@admin_bp.route('/add_department', methods=['POST'])
@login_required
@admin_required
def add_department():
    try:
        department = Department(
            code=request.form['code'],
            name=request.form['name'],
            description=request.form['description']
        )
        db.session.add(department)
        db.session.commit()
        flash('Department added successfully!', 'success')
        return redirect(url_for('admin.manage_departments'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding department: {str(e)}', 'error')
        return redirect(url_for('admin.manage_departments'))

@admin_bp.route('/edit_department/<int:department_id>', methods=['POST'])
@login_required
@admin_required
def edit_department(department_id):
    try:
        department = Department.query.get_or_404(department_id)
        department.code = request.form['code']
        department.name = request.form['name']
        department.description = request.form['description']
        db.session.commit()
        flash('Department updated successfully!', 'success')
        return redirect(url_for('admin.manage_departments'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating department: {str(e)}', 'error')
        return redirect(url_for('admin.manage_departments'))

@admin_bp.route('/delete_department/<int:department_id>', methods=['POST'])
@login_required
@admin_required
def delete_department(department_id):
    try:
        department = Department.query.get_or_404(department_id)
        if department.users or department.courses:
            return jsonify({
                'success': False,
                'message': 'Cannot delete department that has users or courses assigned to it'
            })
        db.session.delete(department)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting department: {str(e)}'
        })

@admin_bp.route('/course/<int:course_id>')
@login_required
@admin_required
def get_course(course_id):
    course = Course.query.get_or_404(course_id)
    return jsonify({
        'id': course.id,
        'code': course.code,
        'name': course.name,
        'description': course.description,
        'department_id': course.department_id,
        'lecturer_id': course.lecturer_id
    })

@admin_bp.route('/add_course', methods=['POST'])
@login_required
@admin_required
def add_course():
    try:
        course = Course(
            code=request.form['code'],
            name=request.form['name'],
            description=request.form['description'],
            department_id=request.form['department_id'],
            lecturer_id=request.form['lecturer_id'] or None
        )
        db.session.add(course)
        db.session.commit()
        flash('Course added successfully!', 'success')
        return redirect(url_for('admin.manage_courses'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding course: {str(e)}', 'error')
        return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/edit_course/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def edit_course(course_id):
    try:
        course = Course.query.get_or_404(course_id)
        course.code = request.form['code']
        course.name = request.form['name']
        course.description = request.form['description']
        course.department_id = request.form['department_id']
        course.lecturer_id = request.form['lecturer_id'] or None
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin.manage_courses'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating course: {str(e)}', 'error')
        return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/delete_course/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    try:
        course = Course.query.get_or_404(course_id)
        if course.sessions:
            return jsonify({
                'success': False,
                'message': 'Cannot delete course that has sessions'
            })
        db.session.delete(course)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting course: {str(e)}'
        })

@admin_bp.route('/manage_lectures')
@login_required
@admin_required
def manage_lectures():
    # Get all lectures with their related course and lecturer information
    lectures = Lecture.query.all()
    return render_template('admin/manage_lectures.html', lectures=lectures)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    try:
        # Get current settings from database or create default
        settings = SystemSettings.query.first()
        form = SystemSettingsForm(obj=settings)
        
        if form.validate_on_submit():
            if not settings:
                settings = SystemSettings()
                db.session.add(settings)
            
            # Update settings from form
            form.populate_obj(settings)
            
            try:
                db.session.commit()
                flash('Settings updated successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating settings: {str(e)}', 'error')
            
            return redirect(url_for('admin.settings'))
        
        return render_template('admin/settings.html', form=form, settings=settings)
    except Exception as e:
        flash(f'Error loading settings: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))
