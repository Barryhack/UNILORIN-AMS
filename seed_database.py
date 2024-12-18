from app import create_app, db
from app.models import User, Department, Course, Lecture, Attendance
from datetime import datetime, timedelta
import random

def seed_database():
    app = create_app()
    with app.app_context():
        # Drop all tables and recreate them
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        # Create Departments
        print("Creating departments...")
        departments = [
            Department(name="Computer Science", code="CSC"),
            Department(name="Electrical Engineering", code="EEE"),
            Department(name="Mechanical Engineering", code="MEE"),
            Department(name="Civil Engineering", code="CVE")
        ]
        db.session.add_all(departments)
        db.session.commit()

        # Create Admin
        print("Creating admin user...")
        admin = User(
            first_name="Admin",
            last_name="User",
            email="admin@unilorin.edu.ng",
            role="admin",
            department_id=departments[0].id,
            matric_number="ADMIN001",  # Admin ID format
            is_biometric_registered=True
        )
        admin.set_password("admin123")
        db.session.add(admin)

        # Create Lecturers
        print("Creating lecturers...")
        lecturers = []
        for i, dept in enumerate(departments):
            lecturer = User(
                first_name=f"Lecturer{i+1}",
                last_name=f"Test",
                email=f"lecturer{i+1}@unilorin.edu.ng",
                role="lecturer",
                department_id=dept.id,
                matric_number=f"LEC{i+1:03d}",  # Lecturer ID format: LEC001, LEC002, etc.
                is_biometric_registered=True
            )
            lecturer.set_password("lecturer123")
            lecturers.append(lecturer)
        db.session.add_all(lecturers)

        # Create Students (10 per department)
        print("Creating students...")
        students = []
        for dept in departments:
            for i in range(10):
                student = User(
                    first_name=f"Student{i+1}",
                    last_name=f"{dept.code}",
                    email=f"student{i+1}.{dept.code.lower()}@unilorin.edu.ng",
                    role="student",
                    department_id=dept.id,
                    matric_number=f"{dept.code}{i+1:03d}",  # Student ID format: CSC001, EEE001, etc.
                    is_biometric_registered=True
                )
                student.set_password("student123")
                students.append(student)
        db.session.add_all(students)
        db.session.commit()

        # Create Courses (2 per lecturer)
        print("Creating courses...")
        courses = []
        for lecturer in lecturers:
            dept_students = [s for s in students if s.department_id == lecturer.department_id]
            for i in range(2):
                course = Course(
                    code=f"{lecturer.department.code}{i+1:03d}",
                    title=f"Test Course {i+1} - {lecturer.department.name}",
                    description=f"Test course {i+1} for {lecturer.department.name}",
                    department_id=lecturer.department_id,
                    lecturer_id=lecturer.id
                )
                # Enroll department students
                course.students.extend(dept_students)
                courses.append(course)
        db.session.add_all(courses)
        db.session.commit()

        # Create Lectures (4 per course, 2 past, 1 today, 1 future)
        print("Creating lectures...")
        lectures = []
        now = datetime.utcnow()
        today = now.replace(hour=9, minute=0, second=0, microsecond=0)
        
        for course in courses:
            # Past lectures
            for i in range(2):
                past_date = today - timedelta(days=i+1)
                lecture = Lecture(
                    course_id=course.id,
                    title=f"Lecture {i+1}",
                    start_time=past_date,
                    end_time=past_date + timedelta(hours=2),
                    room=f"Room {random.randint(1, 10):02d}",
                    status="completed"
                )
                lectures.append(lecture)
            
            # Today's lecture
            lecture = Lecture(
                course_id=course.id,
                title="Today's Lecture",
                start_time=today,
                end_time=today + timedelta(hours=2),
                room=f"Room {random.randint(1, 10):02d}",
                status="in-progress"
            )
            lectures.append(lecture)
            
            # Future lecture
            future_date = today + timedelta(days=1)
            lecture = Lecture(
                course_id=course.id,
                title="Next Lecture",
                start_time=future_date,
                end_time=future_date + timedelta(hours=2),
                room=f"Room {random.randint(1, 10):02d}",
                status="scheduled"
            )
            lectures.append(lecture)
        
        db.session.add_all(lectures)
        db.session.commit()

        # Create Attendance Records (for past and today's lectures)
        print("Creating attendance records...")
        attendances = []
        
        for lecture in lectures:
            if lecture.status in ["completed", "in-progress"]:
                for student in lecture.course.students:
                    # Randomize attendance status for past lectures
                    if lecture.status == "completed":
                        status = random.choices(
                            ["present", "absent", "late"],
                            weights=[0.8, 0.1, 0.1]
                        )[0]
                    else:
                        # For today's lecture, mark some students as present
                        status = random.choices(
                            ["present", "absent"],
                            weights=[0.6, 0.4]
                        )[0]
                    
                    if status != "absent":
                        attendance = Attendance(
                            user_id=student.id,
                            course_id=lecture.course_id,
                            lecture_id=lecture.id,
                            verification_method=random.choice(["rfid", "fingerprint", "both"]),
                            status=status,
                            timestamp=lecture.start_time + timedelta(minutes=random.randint(0, 30))
                        )
                        attendances.append(attendance)
        
        db.session.add_all(attendances)
        db.session.commit()

        print("Database seeded successfully!")
        print("\nTest Accounts:")
        print("Admin:")
        print("  Email: admin@unilorin.edu.ng")
        print("  Password: admin123")
        print("\nLecturers:")
        print("  Email: lecturer1@unilorin.edu.ng (through lecturer4@unilorin.edu.ng)")
        print("  Password: lecturer123")
        print("\nStudents:")
        print("  Email: student1.csc@unilorin.edu.ng (and similar for other departments)")
        print("  Password: student123")

if __name__ == "__main__":
    seed_database()
