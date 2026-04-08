from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional


# ─── Request Schemas ─────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ─── Response Schemas ────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime
    roles: list[str] = []
    permissions: list[str] = []

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int   # seconds


class MessageResponse(BaseModel):
    message: str
    success: bool = True
