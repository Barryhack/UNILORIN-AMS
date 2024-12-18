from app import db

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    system_name = db.Column(db.String(100), default='Attendance Management System')
    academic_year = db.Column(db.String(20), default='2023/2024')
    semester = db.Column(db.String(20), default='First')
    late_threshold = db.Column(db.Integer, default=15)  # minutes
    attendance_threshold = db.Column(db.Integer, default=75)  # percentage
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
