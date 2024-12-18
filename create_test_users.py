from app import db, create_app
from app.models import User, Department, Course, Student, Lecture
from datetime import datetime, timedelta

def create_test_users():
    app = create_app()
    with app.app_context():
        # Create a department
        dept = Department(
            name='Computer Science',
            code='CSC'
        )
        db.session.add(dept)
        db.session.commit()

        # Create admin user
        admin = User(
            id='AD001',
            email='admin@example.com',
            name='Admin User',
            role='admin',
            department_id=dept.id
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Create lecturer user
        lecturer = User(
            id='LC001',
            email='lecturer@example.com',
            name='John Doe',
            role='lecturer',
            department_id=dept.id
        )
        lecturer.set_password('lecturer123')
        db.session.add(lecturer)

        # Create a student user
        student = User(
            id='ST001',
            email='student@example.com',
            name='Jane Smith',
            role='student',
            department_id=dept.id
        )
        student.set_password('student123')
        db.session.add(student)

        db.session.commit()

        # Create student record
        student_record = Student(
            user_id=student.id,
            matric_number='CSC/2023/001',
            level=100,
            department_id=dept.id
        )
        db.session.add(student_record)
        db.session.commit()

        # Create courses
        course1 = Course(
            code='CSC101',
            title='Introduction to Programming',
            description='Basic programming concepts using Python',
            units=3,
            level=100,
            semester=1,
            department_id=dept.id
        )
        db.session.add(course1)

        course2 = Course(
            code='CSC102',
            title='Data Structures',
            description='Fundamental data structures and algorithms',
            units=3,
            level=100,
            semester=2,
            department_id=dept.id
        )
        db.session.add(course2)
        db.session.commit()

        # Enroll student in courses
        student_record.courses.extend([course1, course2])
        db.session.commit()

        # Create lectures for each course
        now = datetime.now()
        for course in [course1, course2]:
            # Past lecture
            past_lecture = Lecture(
                course_id=course.id,
                lecturer_id=lecturer.id,
                date=now - timedelta(days=7),
                start_time=(now - timedelta(days=7)).time(),
                end_time=(now - timedelta(days=7, hours=-2)).time(),
                topic=f"Past Lecture for {course.code}"
            )
            db.session.add(past_lecture)

            # Today's lecture
            today_lecture = Lecture(
                course_id=course.id,
                lecturer_id=lecturer.id,
                date=now,
                start_time=now.time(),
                end_time=(now + timedelta(hours=2)).time(),
                topic=f"Today's Lecture for {course.code}"
            )
            db.session.add(today_lecture)

            # Future lecture
            future_lecture = Lecture(
                course_id=course.id,
                lecturer_id=lecturer.id,
                date=now + timedelta(days=7),
                start_time=(now + timedelta(days=7)).time(),
                end_time=(now + timedelta(days=7, hours=2)).time(),
                topic=f"Future Lecture for {course.code}"
            )
            db.session.add(future_lecture)

        db.session.commit()

        print("Test users and data created successfully!")
        print("\nTest User Credentials:")
        print("Admin - ID: AD001, Password: admin123")
        print("Lecturer - ID: LC001, Password: lecturer123")
        print("Student - ID: ST001, Password: student123")

if __name__ == '__main__':
    create_test_users()
