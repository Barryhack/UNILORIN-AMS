from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models.user import User
from app.models.department import Department
from app.models.course import Course
from app.models.lecture import Lecture
from app import db
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You must be an admin to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get current time
    current_time = datetime.now()

    # Get quick stats
    total_students = User.query.filter_by(role='student').count()
    total_lecturers = User.query.filter_by(role='lecturer').count()
    total_departments = Department.query.count()
    total_courses = Course.query.count()

    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    # Get departments with user counts
    departments = Department.query.all()
    department_stats = []
    for dept in departments:
        student_count = User.query.filter_by(department_id=dept.id, role='student').count()
        lecturer_count = User.query.filter_by(department_id=dept.id, role='lecturer').count()
        department_stats.append({
            'name': dept.name,
            'code': dept.code,
            'student_count': student_count,
            'lecturer_count': lecturer_count
        })

    return render_template('admin/dashboard.html',
                         current_time=current_time,
                         total_students=total_students,
                         total_lecturers=total_lecturers,
                         total_departments=total_departments,
                         total_courses=total_courses,
                         recent_users=recent_users,
                         department_stats=department_stats)

@admin_bp.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register_user():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        user_id = request.form.get('user_id')
        role = request.form.get('role')
        department_id = request.form.get('department_id')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate form data
        if not all([name, email, user_id, role, password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('admin.register_user'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('admin.register_user'))

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('admin.register_user'))

        if User.query.filter_by(user_id=user_id).first():
            flash('User ID already exists.', 'error')
            return redirect(url_for('admin.register_user'))

        # Create new user
        try:
            user = User(
                name=name,
                email=email,
                user_id=user_id,
                role=role,
                department_id=department_id if department_id else None
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('User registered successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error registering user: {str(e)}', 'error')
            return redirect(url_for('admin.register_user'))

    # GET request - show registration form
    departments = Department.query.all()
    return render_template('admin/register_user.html', departments=departments)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/departments')
@login_required
@admin_required
def manage_departments():
    departments = Department.query.all()
    return render_template('admin/manage_departments.html', departments=departments)

@admin_bp.route('/courses')
@login_required
@admin_required
def manage_courses():
    courses = Course.query.all()
    return render_template('admin/manage_courses.html', courses=courses)

@admin_bp.route('/lectures')
@login_required
@admin_required
def manage_lectures():
    lectures = Lecture.query.all()
    return render_template('admin/manage_lectures.html', lectures=lectures)

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    return render_template('admin/settings.html')
