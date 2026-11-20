from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.course import Course, CourseEnrollment
from app.models.user import User
from app.security.passwords import hash_password

DEMO_PASSWORD = "ChangeMe123!"


def get_or_create_user(db, university_id: str, email: str, role: str) -> User:
    user = db.scalar(select(User).where(User.university_id == university_id))
    if user:
        return user

    user = User(
        university_id=university_id,
        email=email,
        password_hash=hash_password(DEMO_PASSWORD),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        get_or_create_user(db, "ADMIN001", "admin@example.com", "admin")
        lecturer = get_or_create_user(db, "LECT001", "lecturer@example.com", "lecturer")
        student = get_or_create_user(db, "STU001", "student@example.com", "student")

        course = db.scalar(select(Course).where(Course.code == "SMART101"))
        if not course:
            course = Course(code="SMART101", name="SmartAttend Demo Course", lecturer_id=lecturer.id)
            db.add(course)
            db.flush()
        elif course.lecturer_id != lecturer.id:
            course.lecturer_id = lecturer.id

        enrollment = db.scalar(
            select(CourseEnrollment).where(
                CourseEnrollment.course_id == course.id,
                CourseEnrollment.student_id == student.id,
            )
        )
        if not enrollment:
            db.add(CourseEnrollment(course_id=course.id, student_id=student.id))

        db.commit()
        print("Demo data is ready.")
        print("Admin:    ADMIN001 / ChangeMe123!")
        print("Lecturer: LECT001  / ChangeMe123!")
        print("Student:  STU001   / ChangeMe123!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
