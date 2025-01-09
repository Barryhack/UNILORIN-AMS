from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.login_log import LoginLog
from app.extensions import db
from app.forms.auth import LoginForm
from urllib.parse import urlparse

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(current_user.get_dashboard_route()))
        
    form = LoginForm()
    if form.validate_on_submit():
        # Try to find user by ID number
        user = User.query.filter_by(id_number=form.login.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return redirect(url_for('auth.login'))
            
            # Update last login time
            user.update_last_login()
            
            login_user(user)
            
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
            except Exception as e:
                db.session.rollback()
                flash('An error occurred during login. Please try again.', 'error')
            
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for(user.get_dashboard_route())
            return redirect(next_page)
        
        # Log failed login attempt
        if user:
            log = LoginLog(
                user_id=user.id,
                status='failed',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
        else:
            log = LoginLog(
                user_id=None,
                status='failed',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                details=f"Invalid ID number: {form.login.data}"
            )
        
        db.session.add(log)
        try:
            db.session.commit()
        except:
            db.session.rollback()
        
        flash('Invalid ID number or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')
