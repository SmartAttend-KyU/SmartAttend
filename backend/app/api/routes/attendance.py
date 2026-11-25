from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.attendance import AttendanceRecord, AttendanceSession
from app.models.course import Course, CourseEnrollment
from app.models.user import User
from app.schemas.attendance import (
    AttendanceResponse,
    AttendanceVerifyRequest,
    CourseResponse,
    SessionCreate,
    SessionResponse,
)
from app.security.dependencies import require_role
from app.services.attendance import (
    current_verification_window,
    session_status,
    utc_now,
    validate_qr_token,
    validate_totp,
)


router = APIRouter(prefix="/attendance", tags=["attendance"])


def _course_or_404(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _session_response(
    db: Session,
    session: AttendanceSession,
    *,
    include_codes: bool,
) -> SessionResponse:
    course = db.get(Course, session.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    status_name = session_status(session)
    window = (
        current_verification_window(session)
        if include_codes and status_name == "active"
        else {}
    )

    return SessionResponse(
        id=session.id,
        course_id=session.course_id,
        course_code=course.code,
        course_name=course.name,
        starts_at=session.starts_at,
        expires_at=session.expires_at,
        ended_at=session.ended_at,
        refresh_interval_seconds=session.refresh_interval_seconds,
        status=status_name,
        totp_code=window.get("totp_code"),
        qr_token=window.get("qr_token"),
        qr_code=window.get("qr_code"),
        qr_expires_at=window.get("qr_expires_at"),
    )


@router.get("/courses", response_model=list[CourseResponse])
def lecturer_courses(
    lecturer: User = Depends(require_role("lecturer")),
    db: Session = Depends(get_db),
):
    courses = db.scalars(
        select(Course)
        .where(Course.lecturer_id == lecturer.id)
        .order_by(Course.code)
    ).all()
    return [
        CourseResponse(id=course.id, code=course.code, name=course.name)
        for course in courses
    ]


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    payload: SessionCreate,
    lecturer: User = Depends(require_role("lecturer")),
    db: Session = Depends(get_db),
):
    course = _course_or_404(db, payload.course_id)
    if course.lecturer_id != lecturer.id:
        raise HTTPException(
            status_code=403,
            detail="Lecturer is not assigned to this course",
        )

    now = utc_now()
    active_session = db.scalar(
        select(AttendanceSession)
        .where(
            AttendanceSession.course_id == course.id,
            AttendanceSession.lecturer_id == lecturer.id,
            AttendanceSession.ended_at.is_(None),
            AttendanceSession.expires_at > now,
        )
        .order_by(AttendanceSession.id.desc())
    )
    if active_session:
        raise HTTPException(
            status_code=409,
            detail="An active attendance session already exists for this course",
        )

    session = AttendanceSession(
        course_id=course.id,
        lecturer_id=lecturer.id,
        starts_at=now,
        expires_at=now + timedelta(minutes=payload.duration_minutes),
        refresh_interval_seconds=payload.refresh_interval_seconds,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return _session_response(db, session, include_codes=True)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    lecturer: User = Depends(require_role("lecturer")),
    db: Session = Depends(get_db),
):
    session = db.get(AttendanceSession, session_id)
    if not session or session.lecturer_id != lecturer.id:
        raise HTTPException(status_code=404, detail="Attendance session not found")

    return _session_response(db, session, include_codes=True)


@router.post("/sessions/{session_id}/end", response_model=SessionResponse)
def end_session(
    session_id: int,
    lecturer: User = Depends(require_role("lecturer")),
    db: Session = Depends(get_db),
):
    session = db.get(AttendanceSession, session_id)
    if not session or session.lecturer_id != lecturer.id:
        raise HTTPException(status_code=404, detail="Attendance session not found")

    if session.ended_at is None:
        session.ended_at = utc_now()
        db.commit()
        db.refresh(session)

    return _session_response(db, session, include_codes=False)


@router.post(
    "/verify",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def verify_attendance(
    payload: AttendanceVerifyRequest,
    student: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    session = db.get(AttendanceSession, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found")

    now = utc_now()
    if session_status(session, now) != "active":
        raise HTTPException(
            status_code=410,
            detail="Attendance session is not active",
        )

    if not validate_qr_token(
        payload.qr_token,
        session.id,
        now,
        interval_seconds=session.refresh_interval_seconds,
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired QR code")

    if not validate_totp(
        session.id,
        payload.totp_code,
        now,
        interval_seconds=session.refresh_interval_seconds,
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired TOTP")

    enrolled = db.scalar(
        select(
            exists().where(
                CourseEnrollment.course_id == session.course_id,
                CourseEnrollment.student_id == student.id,
            )
        )
    )
    if not enrolled:
        raise HTTPException(
            status_code=403,
            detail="Student is not enrolled in this course",
        )

    record = AttendanceRecord(
        session_id=session.id,
        student_id=student.id,
        recorded_at=now,
        verification_method="qr_totp",
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Attendance already recorded for this session",
        )

    return AttendanceResponse(
        id=record.id,
        session_id=record.session_id,
        student_id=record.student_id,
        recorded_at=record.recorded_at,
        verification_method=record.verification_method,
    )
