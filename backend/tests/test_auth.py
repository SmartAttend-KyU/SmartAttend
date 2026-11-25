import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models.user import User
from app.security.passwords import hash_password

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(
        User(
            university_id="STU001",
            email="student@example.com",
            password_hash=hash_password("ChangeMe123!"),
            role="student",
            is_active=True,
        )
    )
    db.commit()
    db.close()


def test_login_returns_bearer_token():
    response = client.post(
        "/api/auth/login",
        json={"university_id": "STU001", "password": "ChangeMe123!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_invalid_password_is_rejected():
    response = client.post(
        "/api/auth/login",
        json={"university_id": "STU001", "password": "WrongPassword!"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_authenticated_user_can_read_me():
    login = client.post(
        "/api/auth/login",
        json={"university_id": "STU001", "password": "ChangeMe123!"},
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["university_id"] == "STU001"
    assert response.json()["role"] == "student"


def test_missing_token_is_rejected():
    response = client.get("/api/auth/me")
    assert response.status_code == 401
