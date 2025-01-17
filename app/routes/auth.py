"""Authentication routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app.forms.auth import LoginForm
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.login_log import LoginLog
from app.extensions import db
from datetime import datetime
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    error = None
    
    if request.method == 'POST':
        logger.info(f"Login attempt from IP: {request.remote_addr}")
        
        if form.validate_on_submit():
            try:
                # Find user by login_id
                user = User.query.filter_by(login_id=form.login.data).first()
                
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
                    db.session.add(login_log)
                    
                    # Create activity log
                    activity_log = ActivityLog(
                        user_id=user.id,
                        action='login',
                        details=f'User logged in from {request.remote_addr}',
                        category='auth',
                        ip_address=request.remote_addr
                    )
                    db.session.add(activity_log)
                    
                    try:
                        db.session.commit()
                    except SQLAlchemyError as e:
                        logger.error(f"Database error during login: {e}")
                        db.session.rollback()
                        error = "Database error occurred. Please try again."
                        return render_template('auth/login.html', form=form, error=error)
                    
                    # Log in the user
                    login_user(user, remember=form.remember.data)
                    logger.info(f"User {user.login_id} logged in successfully")
                    
                    # Redirect based on role
                    if user.role == 'admin':
                        return redirect(url_for('admin.dashboard'))
                    elif user.role == 'lecturer':
                        return redirect(url_for('lecturer.dashboard'))
                    else:
                        return redirect(url_for('student.dashboard'))
                else:
                    error = "Invalid login ID or password"
                    logger.warning(f"Failed login attempt for login_id: {form.login.data}")
                    
                    # Log failed attempt
                    if user:
                        login_log = LoginLog(
                            user_id=user.id,
                            ip_address=request.remote_addr,
                            user_agent=request.user_agent.string,
                            action='login',
                            status='failed'
                        )
                        try:
                            db.session.add(login_log)
                            db.session.commit()
                        except SQLAlchemyError as e:
                            logger.error(f"Error logging failed login: {e}")
                            db.session.rollback()
            except Exception as e:
                logger.error(f"Error during login: {e}")
                error = "An error occurred during login. Please try again."
        else:
            error = "Please check your input and try again."
            for field, errors in form.errors.items():
                for error in errors:
                    logger.warning(f"Form validation error - {field}: {error}")
    
    return render_template('auth/login.html', form=form, error=error)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    try:
        # Create activity log
        activity_log = ActivityLog(
            user_id=current_user.id,
            action='logout',
            details=f'User logged out from {request.remote_addr}',
            ip_address=request.remote_addr,
            timestamp=datetime.utcnow()
        )
        db.session.add(activity_log)
        db.session.commit()
        
        # Log out user after successful transaction
        user_id = current_user.id
        logout_user()
        logger.info(f"User {user_id} logged out successfully")
        flash('You have been logged out.', 'success')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during logout: {str(e)}")
        flash('An error occurred during logout.', 'error')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during logout: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
        
    return redirect(url_parse(url_for('auth.login')).path)

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')
