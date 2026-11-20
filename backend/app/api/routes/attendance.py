from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.attendance import AttendanceRecord, AttendanceSession
from app.models.course import CourseEnrollment
from app.models.user import User
from app.schemas.attendance import (
    AttendanceResponse,
    AttendanceVerifyRequest,
    SessionCreate,
    SessionResponse,
)
from app.security.dependencies import get_current_user, require_role
from app.services.attendance import verification_code

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/sessions", response_model=SessionResponse)
def create_session(
    payload: SessionCreate,
    lecturer: User = Depends(require_role("lecturer", "admin")),
    db: Session = Depends(get_db),
):
    course_exists = db.scalar(select(exists().where(__import__("app.models.course", fromlist=["Course"]).Course.id == payload.course_id)))
    if not course_exists:
        raise HTTPException(status_code=404, detail="Course not found")
    starts = datetime.now(timezone.utc)
    expires = starts + timedelta(minutes=payload.duration_minutes)
    session = AttendanceSession(
        course_id=payload.course_id,
        lecturer_id=lecturer.id,
        starts_at=starts,
        expires_at=expires,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse(
        id=session.id,
        course_id=session.course_id,
        starts_at=session.starts_at,
        expires_at=session.expires_at,
        verification_code=verification_code(session.id, starts),
    )

@router.get("/sessions/{session_id}/code")
def current_code(
    session_id: int,
    lecturer: User = Depends(require_role("lecturer", "admin")),
    db: Session = Depends(get_db),
):
    session = db.get(AttendanceSession, session_id)
    if not session or session.lecturer_id != lecturer.id:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    now = datetime.now(timezone.utc)
    if now >= session.expires_at:
        raise HTTPException(status_code=410, detail="Attendance session has expired")
    return {"session_id": session.id, "verification_code": verification_code(session.id, now), "expires_at": session.expires_at}

@router.post("/verify", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def verify_attendance(
    payload: AttendanceVerifyRequest,
    student: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    session = db.get(AttendanceSession, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found")

    now = datetime.now(timezone.utc)
    if now < session.starts_at or now >= session.expires_at:
        raise HTTPException(status_code=410, detail="Attendance session is not active")

    expected = verification_code(session.id, now)
    if not hmac.compare_digest(payload.verification_code, expected):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    enrolled = db.scalar(select(exists().where(
        CourseEnrollment.course_id == session.course_id,
        CourseEnrollment.student_id == student.id,
    )))
    if not enrolled:
        raise HTTPException(status_code=403, detail="Student is not enrolled in this course")

    record = AttendanceRecord(
        session_id=session.id,
        student_id=student.id,
        recorded_at=now,
        verification_method="rotating_code",
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Attendance already recorded for this session")
    return AttendanceResponse(
        id=record.id,
        session_id=record.session_id,
        student_id=record.student_id,
        recorded_at=record.recorded_at,
        verification_method=record.verification_method,
    )
