"""Authentication & User Schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    user_type: str
    is_active: bool
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()
