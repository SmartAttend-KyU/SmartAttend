from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    course_id: int
    duration_minutes: int = Field(default=15, ge=1, le=180)
    refresh_interval_seconds: int = Field(default=10, ge=5, le=15)


class CourseResponse(BaseModel):
    id: int
    code: str
    name: str


class SessionResponse(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_name: str
    starts_at: datetime
    expires_at: datetime
    ended_at: datetime | None
    refresh_interval_seconds: int
    status: str
    totp_code: str | None = None
    qr_token: str | None = None
    qr_code: str | None = None
    qr_expires_at: datetime | None = None


class StudentSessionResponse(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_name: str
    starts_at: datetime
    expires_at: datetime
    refresh_interval_seconds: int
    status: str


class AttendanceVerifyRequest(BaseModel):
    session_id: int
    qr_token: str = Field(min_length=20, max_length=256)
    totp_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class AttendanceResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    recorded_at: datetime
    verification_method: str


class AttendanceHistoryResponse(BaseModel):
    id: int
    session_id: int
    course_id: int
    course_code: str
    course_name: str
    recorded_at: datetime
    verification_method: str


class AttendanceSummaryResponse(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    attended_sessions: int
    total_sessions: int
    percentage: float
