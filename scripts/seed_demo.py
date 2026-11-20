from app.db.session import Base, SessionLocal, engine
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.security.passwords import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    lecturer = User(
        university_id="LECT001",
        email="lecturer@example.com",
        password_hash=hash_password("ChangeMe123!"),
        role="lecturer",
    )
    student = User(
        university_id="STU001",
        email="student@example.com",
        password_hash=hash_password("ChangeMe123!"),
        role="student",
    )
    course = Course(code="SMART101", name="SmartAttend Demo Course")
    db.add_all([lecturer, student, course])
    db.flush()
    db.add(CourseEnrollment(course_id=course.id, student_id=student.id))
    db.commit()
    print("Demo data created.")
finally:
    db.close()
