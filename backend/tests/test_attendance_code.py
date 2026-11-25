import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from datetime import datetime, timezone

from app.services.attendance import (
    totp_code,
    totp_code_from_secret,
)


def test_totp_is_deterministic_for_same_rotation_window():
    instant = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert totp_code(42, instant) == totp_code(42, instant)


def test_totp_rotates_between_ten_second_windows():
    first = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    second = datetime(2026, 1, 1, 10, 0, 11, tzinfo=timezone.utc)
    assert totp_code(42, first) != totp_code(42, second)


def test_totp_has_six_digits():
    instant = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    code = totp_code(42, instant)
    assert len(code) == 6
    assert code.isdigit()


def test_rfc_6238_sha1_reference_vector():
    # RFC 6238 Appendix B: secret 12345678901234567890, T=59,
    # 30-second step, SHA-1 and 8 digits -> 94287082.
    secret = b"12345678901234567890"
    code = totp_code_from_secret(
        secret,
        datetime.fromtimestamp(59, tz=timezone.utc),
        interval_seconds=30,
        digits=8,
    )
    assert code == "94287082"
