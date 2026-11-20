from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, CurrentUser
from app.security.dependencies import get_current_user
from app.security.jwt import create_access_token
from app.security.passwords import verify_password
from app.services.audit import record_audit_event

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.university_id == payload.university_id))

    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        record_audit_event(
            db,
            event_type="LOGIN_FAILED",
            details=f"university_id={payload.university_id}",
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    record_audit_event(db, event_type="LOGIN_SUCCESS", user_id=user.id)
    db.commit()

    return TokenResponse(access_token=create_access_token(str(user.id), user.role))


@router.get("/me", response_model=CurrentUser)
def me(user: User = Depends(get_current_user)):
    return CurrentUser(
        id=user.id,
        university_id=user.university_id,
        email=user.email,
        role=user.role,
    )
