import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from app.models.course import Course
from app.models.department import Department
from werkzeug.security import generate_password_hash

def add_default_data():
    app = create_app()
    with app.app_context():
        # Add default departments
        departments = [
            Department(code='CSC', name='Computer Science', description='Department of Computer Science'),
            Department(code='EEE', name='Electrical Engineering', description='Department of Electrical and Electronics Engineering'),
            Department(code='MCE', name='Mechanical Engineering', description='Department of Mechanical Engineering')
        ]
        
        for dept in departments:
            existing = Department.query.filter_by(code=dept.code).first()
            if not existing:
                db.session.add(dept)
        
        db.session.commit()

        # Add default admin user if not exists
        admin = User.query.filter_by(email='admin@unilorin.edu.ng').first()
        if not admin:
            admin = User(
                login_id='admin',
                email='admin@unilorin.edu.ng',
                first_name='System',
                last_name='Admin',
                role='admin'
            )
            admin.password = generate_password_hash('admin123')
            admin.is_active = True
            db.session.add(admin)

        # Add some lecturers
        lecturers = [
            {
                'login_id': 'john.doe',
                'email': 'john.doe@unilorin.edu.ng',
                'first_name': 'John',
                'last_name': 'Doe',
                'department': 'CSC'
            },
            {
                'login_id': 'jane.smith',
                'email': 'jane.smith@unilorin.edu.ng',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'department': 'EEE'
            }
        ]

        for lect in lecturers:
            existing = User.query.filter_by(email=lect['email']).first()
            if not existing:
                dept = Department.query.filter_by(code=lect['department']).first()
                lecturer = User(
                    login_id=lect['login_id'],
                    email=lect['email'],
                    first_name=lect['first_name'],
                    last_name=lect['last_name'],
                    role='lecturer'
                )
                lecturer.password = generate_password_hash('password123')
                lecturer.is_active = True
                lecturer.department_id = dept.id if dept else None
                db.session.add(lecturer)

        # Add some students
        students = [
            {
                'login_id': '19123456',
                'email': 'student1@unilorin.edu.ng',
                'first_name': 'Student',
                'last_name': 'One',
                'department': 'CSC'
            },
            {
                'login_id': '19123457',
                'email': 'student2@unilorin.edu.ng',
                'first_name': 'Student',
                'last_name': 'Two',
                'department': 'CSC'
            }
        ]

        for stud in students:
            existing = User.query.filter_by(email=stud['email']).first()
            if not existing:
                dept = Department.query.filter_by(code=stud['department']).first()
                student = User(
                    login_id=stud['login_id'],
                    email=stud['email'],
                    first_name=stud['first_name'],
                    last_name=stud['last_name'],
                    role='student'
                )
                student.password = generate_password_hash('password123')
                student.is_active = True
                student.department_id = dept.id if dept else None
                db.session.add(student)

        # Add some courses
        csc_dept = Department.query.filter_by(code='CSC').first()
        if csc_dept:
            lecturer = User.query.filter_by(email='john.doe@unilorin.edu.ng').first()
            courses = [
                {
                    'code': 'CSC101',
                    'title': 'Introduction to Computer Science',
                    'level': '100',
                    'semester': '1'
                },
                {
                    'code': 'CSC201',
                    'title': 'Programming Fundamentals',
                    'level': '200',
                    'semester': '1'
                }
            ]

            for course in courses:
                existing = Course.query.filter_by(code=course['code']).first()
                if not existing:
                    new_course = Course(
                        code=course['code'],
                        title=course['title'],
                        department_id=csc_dept.id,
                        lecturer_id=lecturer.id if lecturer else None,
                        level=course['level'],
                        semester=course['semester']
                    )
                    db.session.add(new_course)

        db.session.commit()

if __name__ == '__main__':
    add_default_data()
