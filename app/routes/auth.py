from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
from sqlalchemy import String

auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    login = StringField('Email or ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        login_id = request.form.get('login')
        password = request.form.get('password')
        
        if not login_id or not password:
            flash('Please enter both ID/email and password.', 'error')
            return redirect(url_for('auth.login'))
        
        # Try to find user by email first
        user = User.query.filter_by(email=login_id).first()
        if not user:
            # If not found by email, try by ID directly (no casting needed)
            user = User.query.filter_by(id=login_id).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page:
                next_page = url_for(user.get_dashboard_route())
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page)
        
        flash('Invalid login credentials. Please try again.', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))
