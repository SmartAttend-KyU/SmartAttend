from datetime import datetime
from pydantic import BaseModel, Field

class SessionCreate(BaseModel):
    course_id: int
    duration_minutes: int = Field(default=15, ge=1, le=180)

class SessionResponse(BaseModel):
    id: int
    course_id: int
    starts_at: datetime
    expires_at: datetime
    verification_code: str

class AttendanceVerifyRequest(BaseModel):
    session_id: int
    verification_code: str = Field(min_length=4, max_length=16)

class AttendanceResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    recorded_at: datetime
    verification_method: str
