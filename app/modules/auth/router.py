from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.core.security import hash_password, hash_refresh_token
from app.db.models import RefreshToken, User
from app.db.session import get_db
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.modules.auth.service import (
    authenticate_user,
    consume_one_time_token,
    issue_tokens,
    register_user,
    issue_one_time_token,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/status")
def auth_status() -> dict[str, str]:
    return {"status": "authentication module ready"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> User:
    return register_user(db, request)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, request)
    access_token, refresh_token = issue_tokens(db, user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user, access_token, refresh_token = rotate_refresh_token(db, request.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: RefreshRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    stored = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(request.refresh_token))
    )
    if stored is None or stored.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    revoke_refresh_token(db, request.refresh_token)


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == request.email.lower()))
    if user is not None:
        issue_one_time_token(db, user, "password_reset")
    return {"message": "If the account exists, password reset instructions have been sent"}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = consume_one_time_token(db, request.token, "password_reset")
    user.password_hash = hash_password(request.password)
    db.commit()
    return {"message": "Password reset successfully"}


@router.post("/verify-email")
def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = consume_one_time_token(db, request.token, "email_verification")
    user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user