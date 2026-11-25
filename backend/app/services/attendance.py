from __future__ import annotations

import base64
import hashlib
import hmac
import struct
from datetime import datetime, timezone
from io import BytesIO

import qrcode
from qrcode.image.svg import SvgImage

from app.core.config import get_settings


DEFAULT_REFRESH_INTERVAL_SECONDS = 10
MIN_REFRESH_INTERVAL_SECONDS = 5
MAX_REFRESH_INTERVAL_SECONDS = 15
QR_GRACE_SECONDS = 2
TOTP_DIGITS = 6


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def session_status(session, at: datetime | None = None) -> str:
    now = at or utc_now()
    expires_at = _as_utc(session.expires_at)
    if session.ended_at is not None:
        return "ended"
    if now >= expires_at:
        return "expired"
    return "active"


def _session_totp_secret(session_id: int) -> bytes:
    """Derive a unique TOTP secret from the server secret and session ID.

    The secret is never exposed to the browser and does not need to be stored
    separately in PostgreSQL. A database compromise therefore does not reveal
    the TOTP signing key without the application secret.
    """
    settings = get_settings()
    message = f"smartattend:totp:{session_id}".encode("utf-8")
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        message,
        hashlib.sha256,
    ).digest()[:20]


def totp_counter(at: datetime, interval_seconds: int) -> int:
    if interval_seconds < MIN_REFRESH_INTERVAL_SECONDS or interval_seconds > MAX_REFRESH_INTERVAL_SECONDS:
        raise ValueError("TOTP interval must be between 5 and 15 seconds")
    return int(at.timestamp()) // interval_seconds


def totp_code(
    session_id: int,
    at: datetime | None = None,
    *,
    interval_seconds: int = DEFAULT_REFRESH_INTERVAL_SECONDS,
) -> str:
    """Generate an RFC 6238-compatible 6-digit TOTP using SHA-1.

    SmartAttend intentionally uses a configurable 5–15 second time step
    (default 10 seconds) to match the proposal's rotating verification window.
    """
    instant = at or utc_now()
    counter = totp_counter(instant, interval_seconds)
    secret = _session_totp_secret(session_id)
    digest = hmac.new(secret, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{binary % (10 ** TOTP_DIGITS):0{TOTP_DIGITS}d}"


def validate_totp(
    session_id: int,
    submitted_code: str,
    at: datetime,
    *,
    interval_seconds: int,
    grace_seconds: int = QR_GRACE_SECONDS,
) -> bool:
    current_counter = totp_counter(at, interval_seconds)
    candidates = [current_counter]

    boundary = current_counter * interval_seconds
    if at.timestamp() - boundary <= grace_seconds:
        candidates.append(current_counter - 1)

    for counter in candidates:
        if counter < 0:
            continue
        candidate_time = datetime.fromtimestamp(
            counter * interval_seconds, tz=timezone.utc
        )
        expected = totp_code(
            session_id,
            candidate_time,
            interval_seconds=interval_seconds,
        )
        if hmac.compare_digest(submitted_code, expected):
            return True
    return False


def qr_signature(session_id: int, counter: int) -> str:
    settings = get_settings()
    message = f"smartattend:qr:{session_id}:{counter}".encode("utf-8")
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()[:32]


def build_qr_token(session_id: int, counter: int) -> str:
    return f"SA1.{session_id}.{counter}.{qr_signature(session_id, counter)}"


def validate_qr_token(
    token: str,
    session_id: int,
    at: datetime,
    *,
    interval_seconds: int,
    grace_seconds: int = QR_GRACE_SECONDS,
) -> bool:
    try:
        version, token_session_id, token_counter, signature = token.split(".")
        token_session_id = int(token_session_id)
        token_counter = int(token_counter)
    except (ValueError, AttributeError):
        return False

    if version != "SA1" or token_session_id != session_id:
        return False

    expected_signature = qr_signature(session_id, token_counter)
    if not hmac.compare_digest(signature, expected_signature):
        return False

    current_counter = totp_counter(at, interval_seconds)
    if token_counter == current_counter:
        return True

    boundary = current_counter * interval_seconds
    return (
        token_counter == current_counter - 1
        and at.timestamp() - boundary <= grace_seconds
    )


def qr_data_uri(payload: str) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    image = qr.make_image(image_factory=SvgImage)
    buffer = BytesIO()
    image.save(buffer)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def current_verification_window(session, at: datetime | None = None) -> dict[str, object]:
    now = at or utc_now()
    expires_at = _as_utc(session.expires_at)
    counter = totp_counter(now, session.refresh_interval_seconds)
    interval = session.refresh_interval_seconds
    window_end = datetime.fromtimestamp((counter + 1) * interval, tz=timezone.utc)
    qr_token = build_qr_token(session.id, counter)

    return {
        "counter": counter,
        "totp_code": totp_code(
            session.id,
            now,
            interval_seconds=session.refresh_interval_seconds,
        ),
        "qr_token": qr_token,
        "qr_code": qr_data_uri(qr_token),
        "qr_expires_at": min(window_end, expires_at),
    }
