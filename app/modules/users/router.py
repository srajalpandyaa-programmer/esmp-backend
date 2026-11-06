from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.core.security import hash_password
from app.db.models import User
from app.db.session import get_db
from app.modules.users.schemas import UserCreate, UserSummary, UserUpdate


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserSummary])
def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[User]:
    if current_user.role.value == "Employee":
        return [current_user]
    return list(db.scalars(select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)).all())


@router.get("/{user_id}", response_model=UserSummary)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role.value == "Employee" and current_user.id != user_id:
        raise HTTPException(status_code=404, detail="User not found")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role.value not in {"Admin", "Manager"}:
        raise HTTPException(status_code=403, detail="Only administrators or managers can create users")
    if db.scalar(select(User).where(User.email == request.email.lower())):
        raise HTTPException(status_code=409, detail="Email is already registered")
    if db.scalar(select(User).where(User.employee_code == request.employee_code)):
        raise HTTPException(status_code=409, detail="Employee code is already registered")
    if current_user.role.value != "Admin" and request.role.value != "Employee":
        raise HTTPException(status_code=403, detail="Managers can only create employee accounts")
    user = User(
        employee_code=request.employee_code,
        full_name=request.full_name,
        email=request.email.lower(),
        password_hash=hash_password(request.password),
        role=request.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserSummary)
def update_user(
    user_id: str,
    request: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role.value != "Admin":
        raise HTTPException(status_code=403, detail="Only administrators can update users")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
