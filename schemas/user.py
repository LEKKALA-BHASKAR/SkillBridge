from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

VALID_ROLES = {"student", "trainer", "institution", "programme_manager", "monitoring_officer"}


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    institution_id: Optional[int] = None

    model_config = {"str_strip_whitespace": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MonitoringTokenRequest(BaseModel):
    key: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    institution_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
