"""Models package."""
from app.extensions import db

from app.models.user import User
from app.models.course import Course
from app.models.lecture import Lecture
from app.models.attendance import Attendance
from app.models.department import Department
from app.models.notification import Notification
from app.models.login_log import LoginLog
from app.models.activity_log import ActivityLog
from app.models.course_student import CourseStudent

__all__ = [
    'User',
    'Course',
    'Lecture',
    'Attendance',
    'Department',
    'Notification',
    'LoginLog',
    'ActivityLog',
    'CourseStudent'
]
