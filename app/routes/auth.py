from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.login_log import LoginLog
from app.extensions import db, csrf
from app.forms.auth import LoginForm
from urllib.parse import urlparse
from flask_wtf.csrf import generate_csrf
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(current_user.get_dashboard_route()))
        
    form = LoginForm()
    
    if request.method == 'GET':
        # Generate a new CSRF token for the form
        csrf_token = generate_csrf()
        session['csrf_token'] = csrf_token
        return render_template('auth/login.html', form=form, csrf_token=csrf_token)
        
    if request.method == 'POST':
        # Log form data for debugging
        logger.info(f"Form data received: {request.form}")
        logger.info(f"Form validation result: {form.validate()}")
        if not form.validate():
            logger.error(f"Form validation errors: {form.errors}")
        
        # Validate CSRF token
        token = request.form.get('csrf_token')
        logger.info(f"Received CSRF token: {token}")
        logger.info(f"Session CSRF token: {session.get('csrf_token')}")
        if not token or token != session.get('csrf_token'):
            flash('Invalid CSRF token. Please try again.', 'error')
            return redirect(url_for('auth.login'))
            
        if form.validate():
            # Try to find user by ID number
            id_number = form.login.data.strip()
            password = form.password.data
            
            logger.info(f"Attempting login with ID: {id_number}")
            
            # List all users in database for debugging
            all_users = User.query.all()
            logger.info(f"All users in database: {[(u.id_number, u.email) for u in all_users]}")
            
            user = User.query.filter_by(id_number=id_number).first()
            logger.info(f"User found: {user is not None}")
            
            if user:
                logger.info(f"Found user: ID={user.id_number}, Email={user.email}, Role={user.role}")
                password_check = user.check_password(password)
                logger.info(f"Password check result: {password_check}")
            
            if user and user.check_password(password):
                if not user.is_active:
                    flash('Your account has been deactivated. Please contact an administrator.', 'error')
                    return redirect(url_for('auth.login'))
                
                # Update last login time
                user.update_last_login()
                
                login_user(user, remember=form.remember.data)
                
                # Log successful login
                log = LoginLog(
                    user_id=user.id,
                    status='success',
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.add(log)
                
                try:
                    db.session.commit()
                    flash('Logged in successfully!', 'success')
                    logger.info(f"User {user.email} logged in successfully")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error during login: {str(e)}")
                    flash('An error occurred during login. Please try again.', 'error')
                
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for(user.get_dashboard_route())
                return redirect(next_page)
            else:
                if user:
                    logger.error(f"Password check failed for user {id_number}")
                else:
                    logger.error(f"No user found with ID {id_number}")
                flash('Invalid ID number or password.', 'error')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{error}', 'error')
                    logger.error(f"Form validation error - {field}: {error}")
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')
