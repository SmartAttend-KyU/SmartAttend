import os

os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key"
os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.session import Base, get_db
from app.main import app
from app.models.attendance import AttendanceSession
from app.models.course import Course, CourseEnrollment
from app.models.user import User
from app.security.passwords import hash_password

get_settings.cache_clear()

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _headers_for(university_id: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"university_id": university_id, "password": "ChangeMe123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def setup_function():
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    lecturer = User(
        university_id="LECT001",
        email="lecturer@example.com",
        password_hash=hash_password("ChangeMe123!"),
        role="lecturer",
        is_active=True,
    )
    student = User(
        university_id="STU001",
        email="student@example.com",
        password_hash=hash_password("ChangeMe123!"),
        role="student",
        is_active=True,
    )
    other_student = User(
        university_id="STU002",
        email="student2@example.com",
        password_hash=hash_password("ChangeMe123!"),
        role="student",
        is_active=True,
    )
    db.add_all([lecturer, student, other_student])
    db.flush()

    course = Course(code="SMART101", name="SmartAttend Demo Course", lecturer_id=lecturer.id)
    db.add(course)
    db.flush()
    db.add(CourseEnrollment(course_id=course.id, student_id=student.id))
    db.commit()
    db.close()


def _create_session() -> dict:
    response = client.post(
        "/api/attendance/sessions",
        headers=_headers_for("LECT001"),
        json={"course_id": 1, "duration_minutes": 15, "refresh_interval_seconds": 10},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_student_sees_only_active_sessions_for_enrolled_courses():
    session = _create_session()
    response = client.get("/api/attendance/student/sessions", headers=_headers_for("STU001"))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == session["id"]
    assert body[0]["course_code"] == "SMART101"
    assert "totp_code" not in body[0]
    assert "qr_token" not in body[0]


def test_non_enrolled_student_cannot_see_active_session():
    _create_session()
    response = client.get("/api/attendance/student/sessions", headers=_headers_for("STU002"))

    assert response.status_code == 200
    assert response.json() == []


def test_student_can_verify_attendance_and_history_is_created():
    session = _create_session()
    verify = client.post(
        "/api/attendance/verify",
        headers=_headers_for("STU001"),
        json={
            "session_id": session["id"],
            "qr_token": session["qr_token"],
            "totp_code": session["totp_code"],
        },
    )
    assert verify.status_code == 201, verify.text

    history = client.get("/api/attendance/student/history", headers=_headers_for("STU001"))
    assert history.status_code == 200
    body = history.json()
    assert len(body) == 1
    assert body[0]["course_code"] == "SMART101"
    assert body[0]["verification_method"] == "qr_totp"


def test_duplicate_student_verification_is_rejected():
    session = _create_session()
    payload = {
        "session_id": session["id"],
        "qr_token": session["qr_token"],
        "totp_code": session["totp_code"],
    }
    first = client.post("/api/attendance/verify", headers=_headers_for("STU001"), json=payload)
    assert first.status_code == 201

    second = client.post("/api/attendance/verify", headers=_headers_for("STU001"), json=payload)
    assert second.status_code == 409


def test_student_cannot_access_lecturer_course_endpoint():
    response = client.get("/api/attendance/courses", headers=_headers_for("STU001"))
    assert response.status_code == 403


def test_student_summary_reports_attendance_percentage():
    _create_session()
    response = client.get("/api/attendance/student/summary", headers=_headers_for("STU001"))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["course_code"] == "SMART101"
    assert body[0]["attended_sessions"] == 0
    assert body[0]["total_sessions"] == 1
    assert body[0]["percentage"] == 0.0
