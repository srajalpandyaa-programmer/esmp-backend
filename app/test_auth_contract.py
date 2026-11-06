import pytest
from pydantic import ValidationError

from app.db.models import RoleName
from app.modules.auth.schemas import RegisterRequest


def test_public_registration_does_not_accept_a_role() -> None:
    request = RegisterRequest(
        employee_code="EMP-001",
        full_name="Test Employee",
        email="employee@example.com",
        password="secure-password",
    )

    assert request.model_dump() == {
        "employee_code": "EMP-001",
        "full_name": "Test Employee",
        "email": "employee@example.com",
        "password": "secure-password",
    }


def test_public_registration_rejects_privileged_role_field() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            employee_code="EMP-001",
            full_name="Test Employee",
            email="employee@example.com",
            password="secure-password",
            role=RoleName.ADMIN,
        )
