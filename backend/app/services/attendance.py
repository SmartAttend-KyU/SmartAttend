from datetime import datetime, timezone
import hashlib
import hmac
from app.core.config import get_settings

ROTATION_SECONDS = 30

def verification_code(session_id: int, at: datetime | None = None) -> str:
    settings = get_settings()
    instant = at or datetime.now(timezone.utc)
    bucket = int(instant.timestamp()) // ROTATION_SECONDS
    message = f"attendance:{session_id}:{bucket}".encode()
    digest = hmac.new(settings.secret_key.encode(), message, hashlib.sha256).digest()
    value = int.from_bytes(digest[:4], "big") % 1_000_000
    return f"{value:06d}"
