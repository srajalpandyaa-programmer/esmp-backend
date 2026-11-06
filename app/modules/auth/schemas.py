from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import validate_password_bytes
from app.db.models import RoleName


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_code: str = Field(min_length=2, max_length=50)
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    _validate_password = field_validator("password")(validate_password_bytes)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    _validate_password = field_validator("password")(validate_password_bytes)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=8, max_length=72)

    _validate_password = field_validator("password")(validate_password_bytes)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=20)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_code: str
    full_name: str
    email: EmailStr
    role: RoleName
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse