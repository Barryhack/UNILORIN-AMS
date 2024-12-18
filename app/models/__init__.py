from app import db
from .user import User
from .course import Course
from .department import Department
from .lecture import Lecture
from .attendance import Attendance
from .student import Student, student_courses
from .system_settings import SystemSettings

__all__ = [
    'User',
    'Department',
    'Course',
    'student_courses',
    'Lecture',
    'Attendance',
    'SystemSettings',
    'Student'
]
