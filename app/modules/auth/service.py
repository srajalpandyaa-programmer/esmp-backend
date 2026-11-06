from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.models import OneTimeToken, RefreshToken, RoleName, User
from app.modules.auth.schemas import LoginRequest, RegisterRequest


def register_user(db: Session, request: RegisterRequest) -> User:
    email = request.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    existing_code = db.scalar(select(User).where(User.employee_code == request.employee_code))
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Employee code is already registered"
        )
    user = User(
        employee_code=request.employee_code,
        full_name=request.full_name,
        email=email,
        password_hash=hash_password(request.password),
        role=RoleName.EMPLOYEE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, request: LoginRequest) -> User:
    user = db.scalar(select(User).where(User.email == request.email.lower()))
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    raw_refresh, refresh_hash = create_refresh_token()
    settings = get_settings()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    db.commit()
    return create_access_token(user.id, user.role.value), raw_refresh


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, str, str]:
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token)))
    if (
        stored is None
        or stored.revoked_at is not None
        or stored.expires_at <= datetime.now(UTC)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    stored.revoked_at = datetime.now(UTC)
    db.flush()
    access, refresh = issue_tokens(db, stored.user)
    return stored.user, access, refresh


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    stored = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    if stored is None or stored.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    stored.revoked_at = datetime.now(UTC)
    db.commit()


def issue_one_time_token(db: Session, user: User, purpose: str) -> str:
    raw = secrets.token_urlsafe(48)
    db.add(
        OneTimeToken(
            user_id=user.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            purpose=purpose,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    db.commit()
    return raw


def consume_one_time_token(db: Session, raw: str, purpose: str) -> User:
    token = db.scalar(
        select(OneTimeToken).where(
            OneTimeToken.token_hash == hashlib.sha256(raw.encode()).hexdigest(),
            OneTimeToken.purpose == purpose,
        )
    )
    if token is None or token.used_at is not None or token.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token owner")
    token.used_at = datetime.now(UTC)
    db.commit()
    return user