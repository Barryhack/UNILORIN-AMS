from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.attendance import Attendance
from app.models.user import User
from app.models.notification import Notification
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import re
import io
import csv
import xlsxwriter

lecturer_bp = Blueprint('lecturer', __name__)

def lecturer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'lecturer':
            flash('You must be a lecturer to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@lecturer_bp.route('/dashboard')
@login_required
@lecturer_required
def dashboard():
    # Get current time
    current_time = datetime.now()

    # Get quick stats
    stats = {
        'total_courses': Course.query.filter_by(lecturer_id=current_user.id).count(),
        'total_lectures': Lecture.query.filter_by(lecturer_id=current_user.id).count(),
        'total_students': sum([course.enrolled_students.count() for course in current_user.courses]),
        'today_lectures': Lecture.query.filter(
            Lecture.lecturer_id == current_user.id,
            Lecture.date == current_time.date()
        ).count()
    }

    # Get upcoming lectures (next 7 days)
    upcoming_lectures = Lecture.query.filter(
        Lecture.lecturer_id == current_user.id,
        Lecture.date >= current_time.date(),
        Lecture.date <= current_time.date() + timedelta(days=7)
    ).order_by(Lecture.date, Lecture.start_time).all()

    # Get recent attendance records
    recent_attendances = Attendance.query.join(Lecture).filter(
        Lecture.lecturer_id == current_user.id
    ).order_by(Attendance.timestamp.desc()).limit(10).all()

    # Get unread notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()

    return render_template('lecturer/dashboard.html',
                         stats=stats,
                         upcoming_lectures=upcoming_lectures,
                         recent_attendances=recent_attendances,
                         notifications=notifications)

@lecturer_bp.route('/courses')
@login_required
@lecturer_required
def view_courses():
    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    return render_template('lecturer/courses.html', courses=courses)

@lecturer_bp.route('/take-attendance/<int:lecture_id>', methods=['GET', 'POST'])
@login_required
@lecturer_required
def take_attendance(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    
    if request.method == 'POST':
        attendance_data = request.get_json()
        for student_id, status in attendance_data.items():
            attendance = Attendance(
                lecture_id=lecture_id,
                student_id=student_id,
                status=status,
                marked_by_id=current_user.id,
                verification_method='manual'
            )
            db.session.add(attendance)
        
        db.session.commit()
        flash('Attendance has been recorded successfully.', 'success')
        return jsonify({'status': 'success'})

    students = User.query.filter_by(role='student').join(
        Course.enrolled_students
    ).filter(Course.id == lecture.course_id).all()
    
    return render_template('lecturer/take_attendance.html',
                         lecture=lecture,
                         students=students)

@lecturer_bp.route('/attendance-records')
@login_required
@lecturer_required
def attendance_records():
    course_id = request.args.get('course_id', type=int)
    lecture_id = request.args.get('lecture_id', type=int)
    student_id = request.args.get('student_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = Attendance.query.join(Lecture).filter(Lecture.lecturer_id == current_user.id)

    if course_id:
        query = query.filter(Lecture.course_id == course_id)
    if lecture_id:
        query = query.filter(Attendance.lecture_id == lecture_id)
    if student_id:
        query = query.filter(Attendance.student_id == student_id)
    if date_from:
        query = query.filter(Lecture.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Lecture.date <= datetime.strptime(date_to, '%Y-%m-%d').date())

    attendances = query.order_by(Lecture.date.desc(), Lecture.start_time.desc()).all()

    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    students = User.query.filter_by(role='student').join(
        Course.enrolled_students
    ).filter(Course.lecturer_id == current_user.id).all()

    return render_template('lecturer/attendance_records.html',
                         attendances=attendances,
                         courses=courses,
                         students=students)

@lecturer_bp.route('/reports')
@login_required
@lecturer_required
def reports():
    course_id = request.args.get('course_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    
    if course_id:
        course = Course.query.get_or_404(course_id)
        students = User.query.filter_by(role='student').join(
            Course.enrolled_students
        ).filter(Course.id == course_id).all()
        
        attendance_stats = []
        for student in students:
            query = Attendance.query.join(Lecture).filter(
                Lecture.course_id == course_id,
                Attendance.student_id == student.id
            )
            
            if date_from:
                query = query.filter(Lecture.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
            if date_to:
                query = query.filter(Lecture.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
            
            total = query.count()
            present = query.filter(Attendance.status == 'present').count()
            
            attendance_stats.append({
                'student': student,
                'total': total,
                'present': present,
                'percentage': round((present / total * 100) if total > 0 else 0, 2)
            })
        
        return render_template('lecturer/reports.html',
                             courses=courses,
                             selected_course=course,
                             attendance_stats=attendance_stats)
    
    return render_template('lecturer/reports.html', courses=courses)

@lecturer_bp.route('/profile')
@login_required
@lecturer_required
def profile():
    # Get lecturer's activity history
    activity_history = (Attendance.query
                       .join(Lecture)
                       .filter(Lecture.lecturer_id == current_user.id)
                       .order_by(Attendance.timestamp.desc())
                       .limit(10)
                       .all())

    return render_template('lecturer/profile.html',
                         activity_history=activity_history)

@lecturer_bp.route('/settings')
@login_required
@lecturer_required
def settings():
    return render_template('lecturer/settings.html')

@lecturer_bp.route('/settings/profile', methods=['POST'])
@login_required
@lecturer_required
def update_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('lecturer.settings'))

        # Check if email is already taken by another user
        existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            flash('This email is already registered.', 'error')
            return redirect(url_for('lecturer.settings'))

        # Update user profile
        current_user.name = name
        current_user.email = email
        current_user.phone = phone

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
            current_app.logger.error(f"Error updating profile for user {current_user.id}: {str(e)}")

    return redirect(url_for('lecturer.settings'))

@lecturer_bp.route('/settings/password', methods=['POST'])
@login_required
@lecturer_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('lecturer.settings'))

        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('lecturer.settings'))

        # Validate password strength
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return redirect(url_for('lecturer.settings'))

        try:
            # Update password
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully!', 'success')

            # Create an audit log
            log_entry = AuditLog(
                user_id=current_user.id,
                action='password_change',
                details='Password changed successfully'
            )
            db.session.add(log_entry)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your password.', 'error')
            current_app.logger.error(f"Error changing password for user {current_user.id}: {str(e)}")

    return redirect(url_for('lecturer.settings'))

@lecturer_bp.route('/settings/notifications', methods=['POST'])
@login_required
@lecturer_required
def update_notifications():
    if request.method == 'POST':
        email_notifications = request.form.get('email_notifications') == 'on'
        browser_notifications = request.form.get('browser_notifications') == 'on'
        attendance_reminders = request.form.get('attendance_reminders') == 'on'

        try:
            # Update user settings
            if not current_user.settings:
                current_user.settings = UserSettings()

            current_user.settings.email_notifications = email_notifications
            current_user.settings.browser_notifications = browser_notifications
            current_user.settings.attendance_reminders = attendance_reminders

            db.session.commit()
            flash('Notification preferences updated successfully!', 'success')

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your notification preferences.', 'error')
            current_app.logger.error(f"Error updating notification settings for user {current_user.id}: {str(e)}")

    return redirect(url_for('lecturer.settings'))

@lecturer_bp.route('/settings/export', methods=['POST'])
@login_required
@lecturer_required
def export_data():
    export_format = request.form.get('format', 'csv')
    
    try:
        # Get the user's data
        courses = Course.query.filter_by(lecturer_id=current_user.id).all()
        lectures = Lecture.query.filter_by(lecturer_id=current_user.id).all()
        attendance_records = (Attendance.query
                            .join(Lecture)
                            .filter(Lecture.lecturer_id == current_user.id)
                            .all())

        if export_format == 'csv':
            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Course Code', 'Course Title', 'Date', 'Time', 'Student', 'Status'])
            
            # Write data
            for record in attendance_records:
                writer.writerow([
                    record.lecture.course.code,
                    record.lecture.course.title,
                    record.lecture.date.strftime('%Y-%m-%d'),
                    record.lecture.start_time.strftime('%H:%M'),
                    record.student.name,
                    record.status
                ])
            
            # Create response
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'attendance_records_{datetime.now().strftime("%Y%m%d")}.csv'
            )

        elif export_format == 'excel':
            # Generate Excel
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # Add headers
            headers = ['Course Code', 'Course Title', 'Date', 'Time', 'Student', 'Status']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)

            # Add data
            for row, record in enumerate(attendance_records, start=1):
                worksheet.write(row, 0, record.lecture.course.code)
                worksheet.write(row, 1, record.lecture.course.title)
                worksheet.write(row, 2, record.lecture.date.strftime('%Y-%m-%d'))
                worksheet.write(row, 3, record.lecture.start_time.strftime('%H:%M'))
                worksheet.write(row, 4, record.student.name)
                worksheet.write(row, 5, record.status)

            workbook.close()
            output.seek(0)

            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'attendance_records_{datetime.now().strftime("%Y%m%d")}.xlsx'
            )

        elif export_format == 'pdf':
            # For PDF, we'll generate a simple HTML file that can be printed to PDF by the browser
            html_content = '''
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f2f2f2; }
                    h1 { text-align: center; }
                </style>
            </head>
            <body>
                <h1>Attendance Records</h1>
                <table>
                    <tr>
                        <th>Course Code</th>
                        <th>Course Title</th>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Student</th>
                        <th>Status</th>
                    </tr>
            '''
            
            for record in attendance_records:
                html_content += f'''
                    <tr>
                        <td>{record.lecture.course.code}</td>
                        <td>{record.lecture.course.title}</td>
                        <td>{record.lecture.date.strftime('%Y-%m-%d')}</td>
                        <td>{record.lecture.start_time.strftime('%H:%M')}</td>
                        <td>{record.student.name}</td>
                        <td>{record.status}</td>
                    </tr>
                '''
            
            html_content += '''
                </table>
                <script>
                    window.onload = function() { window.print(); }
                </script>
            </body>
            </html>
            '''
            
            return html_content, 200, {
                'Content-Type': 'text/html',
                'Content-Disposition': f'inline; filename=attendance_records_{datetime.now().strftime("%Y%m%d")}.html'
            }

    except Exception as e:
        flash('An error occurred while exporting your data.', 'error')
        current_app.logger.error(f"Error exporting data for user {current_user.id}: {str(e)}")
        return redirect(url_for('lecturer.settings'))

@lecturer_bp.route('/api/mark-notification-read/<int:notification_id>', methods=['POST'])
@login_required
@lecturer_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@lecturer_bp.route('/api/get-course-stats/<int:course_id>')
@login_required
@lecturer_required
def get_course_stats(course_id):
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Get attendance statistics for the past 30 days
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    attendance_stats = (db.session.query(
        Lecture.date,
        func.count(Attendance.id).label('count')
    )
    .join(Attendance)
    .filter(
        Lecture.course_id == course_id,
        Lecture.date >= thirty_days_ago
    )
    .group_by(Lecture.date)
    .order_by(Lecture.date)
    .all())

    return jsonify({
        'dates': [str(date) for date, _ in attendance_stats],
        'counts': [count for _, count in attendance_stats]
    })
