from datetime import datetime, timezone
from app.services.attendance import verification_code

def test_verification_code_is_deterministic_for_same_rotation():
    instant = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert verification_code(42, instant) == verification_code(42, instant)

def test_verification_code_rotates_between_time_buckets():
    first = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    second = datetime(2026, 1, 1, 10, 0, 31, tzinfo=timezone.utc)
    assert verification_code(42, first) != verification_code(42, second)

def test_verification_code_has_six_digits():
    instant = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    code = verification_code(42, instant)
    assert len(code) == 6
    assert code.isdigit()
