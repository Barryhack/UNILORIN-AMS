"""Models package."""
from app.extensions import db

# Create a new MetaData instance
metadata = db.MetaData()

# Import all models to register them with MetaData
from .user import User
from .course import Course
from .department import Department
from .attendance import Attendance
from .course_student import CourseStudent
from .login_log import LoginLog
from .activity_log import ActivityLog
from .notification import Notification
from .lecture import Lecture

# List all models for easy access
__all__ = [
    'User',
    'Course',
    'Department',
    'Attendance',
    'CourseStudent',
    'LoginLog',
    'ActivityLog',
    'Notification',
    'Lecture',
    'metadata'
]
