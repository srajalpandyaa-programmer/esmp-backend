from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import validate_password_bytes
from app.db.models import RoleName


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_code: str
    full_name: str
    email: EmailStr
    role: RoleName
    department_id: UUID | None
    is_active: bool


class UserCreate(BaseModel):
    employee_code: str = Field(min_length=2, max_length=50)
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: RoleName = RoleName.EMPLOYEE

    _validate_password = field_validator("password")(validate_password_bytes)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    role: RoleName | None = None
    is_active: bool | None = None
