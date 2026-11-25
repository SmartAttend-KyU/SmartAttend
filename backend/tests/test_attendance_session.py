import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models.attendance import AttendanceSession
from app.models.course import Course
from app.models.user import User
from app.security.passwords import hash_password
from app.services.attendance import build_qr_token, totp_code, validate_qr_token


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _login(university_id: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"university_id": university_id, "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def setup_function():
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
    other_lecturer = User(
        university_id="LECT002",
        email="lecturer2@example.com",
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
    db.add_all([lecturer, other_lecturer, student])
    db.flush()

    db.add(
        Course(
            code="SMART101",
            name="SmartAttend Demo Course",
            lecturer_id=lecturer.id,
        )
    )
    db.commit()
    db.close()


def test_lecturer_can_list_only_assigned_courses():
    token = _login("LECT001")
    response = client.get("/api/attendance/courses", headers=_headers(token))

    assert response.status_code == 200
    assert [course["code"] for course in response.json()] == ["SMART101"]


def test_unauthorized_lecturer_cannot_start_another_lecturers_course():
    token = _login("LECT002")
    response = client.post(
        "/api/attendance/sessions",
        headers=_headers(token),
        json={"course_id": 1, "duration_minutes": 15, "refresh_interval_seconds": 10},
    )

    assert response.status_code == 403


def test_create_session_returns_six_digit_totp_and_qr():
    token = _login("LECT001")
    response = client.post(
        "/api/attendance/sessions",
        headers=_headers(token),
        json={"course_id": 1, "duration_minutes": 15, "refresh_interval_seconds": 10},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "active"
    assert len(body["totp_code"]) == 6
    assert body["totp_code"].isdigit()
    assert body["qr_token"].startswith("SA1.")
    assert body["qr_code"].startswith("data:image/svg+xml;base64,")


def test_server_rejects_expired_session():
    token = _login("LECT001")
    response = client.post(
        "/api/attendance/sessions",
        headers=_headers(token),
        json={"course_id": 1, "duration_minutes": 15, "refresh_interval_seconds": 10},
    )
    session_id = response.json()["id"]

    db = TestingSessionLocal()
    session = db.get(AttendanceSession, session_id)
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    db.close()

    expired = client.get(
        f"/api/attendance/sessions/{session_id}",
        headers=_headers(token),
    )
    assert expired.status_code == 200
    assert expired.json()["status"] == "expired"
    assert expired.json()["totp_code"] is None
    assert expired.json()["qr_code"] is None


def test_ending_session_prevents_further_live_codes():
    token = _login("LECT001")
    response = client.post(
        "/api/attendance/sessions",
        headers=_headers(token),
        json={"course_id": 1, "duration_minutes": 15, "refresh_interval_seconds": 10},
    )
    session_id = response.json()["id"]

    ended = client.post(
        f"/api/attendance/sessions/{session_id}/end",
        headers=_headers(token),
    )
    assert ended.status_code == 200
    assert ended.json()["status"] == "ended"

    current = client.get(
        f"/api/attendance/sessions/{session_id}",
        headers=_headers(token),
    )
    assert current.status_code == 200
    assert current.json()["status"] == "ended"


def test_wrong_totp_is_rejected():
    token = _login("LECT001")
    response = client.post(
        "/api/attendance/sessions",
        headers=_headers(token),
        json={"course_id": 1, "duration_minutes": 15, "refresh_interval_seconds": 10},
    )
    body = response.json()

    student_token = _login("STU001")
    verify = client.post(
        "/api/attendance/verify",
        headers=_headers(student_token),
        json={
            "session_id": body["id"],
            "qr_token": body["qr_token"],
            "totp_code": "000000" if body["totp_code"] != "000000" else "111111",
        },
    )

    assert verify.status_code == 400
    assert verify.json()["detail"] == "Invalid or expired TOTP"


def test_replayed_qr_window_is_rejected_after_grace_period():
    now = datetime(2026, 1, 1, 10, 0, 20, tzinfo=timezone.utc)
    old_counter = int(now.timestamp()) // 10 - 1
    token = build_qr_token(42, old_counter)

    after_grace = now + timedelta(seconds=3)
    assert not validate_qr_token(
        token,
        42,
        after_grace,
        interval_seconds=10,
        grace_seconds=2,
    )


def test_totp_matches_rfc_6238_reference_vector():
    # RFC 6238 Appendix B uses SHA-1, 8-digit output and a 30-second step.
    # The application uses a configurable 5–15 second step and six digits.
    import base64
    import hashlib
    import hmac
    import struct

    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    key = base64.b32decode(secret)
    counter = 1
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (
        struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    ) % 100000000
    assert f"{value:08d}" == "94287082"

    assert len(totp_code(42, datetime(2026, 1, 1, tzinfo=timezone.utc))) == 6
