"""Models package initialization"""
from app.extensions import db

from app.models.user import User
from app.models.department import Department
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.attendance import Attendance
from app.models.system_settings import SystemSettings
from app.models.login_log import LoginLog
from app.models.activity_log import ActivityLog
from app.models.faculty import Faculty
from app.models.student import Student

__all__ = [
    'User',
    'Department',
    'Course',
    'Lecture',
    'Attendance',
    'SystemSettings',
    'LoginLog',
    'ActivityLog',
    'Faculty',
    'Student'
]
