from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app.forms.auth import LoginForm
from app.models import User, LoginLog, ActivityLog
from app.extensions import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    
    if request.method == 'POST':
        logger.info(f"Login attempt from IP: {request.remote_addr}")
        
        if form.validate_on_submit():
            login_id = form.login.data
            logger.info(f"Attempting login with ID: {login_id}")
            
            user = User.query.filter_by(login_id=login_id).first()
            
            if user and user.verify_password(form.password.data):
                # Update last login
                user.last_login = datetime.utcnow()
                
                # Create login log
                login_log = LoginLog(
                    user_id=user.id,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    action='login',
                    status='success'
                )
                
                # Create activity log
                activity_log = ActivityLog(
                    user_id=user.id,
                    action='login',
                    details=f'User logged in from {request.remote_addr}'
                )
                
                try:
                    db.session.add(login_log)
                    db.session.add(activity_log)
                    db.session.commit()
                    
                    # Log in user
                    login_user(user, remember=form.remember.data)
                    logger.info(f"User {login_id} logged in successfully")
                    
                    # Redirect to next page or default
                    next_page = request.args.get('next')
                    if not next_page or url_parse(next_page).netloc != '':
                        if user.role == 'admin':
                            next_page = url_for('admin.dashboard')
                        elif user.role == 'lecturer':
                            next_page = url_for('lecturer.dashboard')
                        else:
                            next_page = url_for('student.dashboard')
                    return redirect(next_page)
                    
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error during login: {str(e)}")
                    flash('An error occurred during login. Please try again.', 'error')
            else:
                logger.warning(f"Failed login attempt for ID: {login_id}")
                flash('Invalid username or password', 'error')
                
                # Log failed login attempt
                try:
                    login_log = LoginLog(
                        user_id=user.id if user else None,
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string,
                        action='login',
                        status='failed'
                    )
                    db.session.add(login_log)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Error logging failed login attempt: {str(e)}")
        else:
            logger.warning("Form validation failed")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'error')
    
    # Pass next parameter to template
    next_page = request.args.get('next')
    return render_template('auth/login.html', form=form, next=next_page)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    try:
        # Create activity log
        activity_log = ActivityLog(
            user_id=current_user.id,
            action='logout',
            details=f'User logged out from {request.remote_addr}'
        )
        db.session.add(activity_log)
        db.session.commit()
        
        # Log out user
        logout_user()
        flash('You have been logged out.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during logout: {str(e)}")
        flash('An error occurred during logout.', 'error')
        
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')
