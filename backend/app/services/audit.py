from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit_event(
    db: Session,
    *,
    event_type: str,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            created_at=datetime.now(timezone.utc),
        )
    )
