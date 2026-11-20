from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    university_id: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CurrentUser(BaseModel):
    id: int
    university_id: str
    email: EmailStr
    role: str
