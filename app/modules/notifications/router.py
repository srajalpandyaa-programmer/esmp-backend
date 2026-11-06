from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.db.models import Notification, User
from app.db.session import get_db
from app.modules.notifications.schemas import NotificationResponse


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.recipient_id == user.id)
            .order_by(Notification.created_at.desc()).offset(offset).limit(min(limit, 100))
        ).all()
    )


@router.patch("/read-all", status_code=204)
def mark_all_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    notifications = db.scalars(
        select(Notification).where(
            Notification.recipient_id == user.id,
            Notification.is_read.is_(False),
        )
    ).all()
    for notification in notifications:
        notification.is_read = True
    db.commit()


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.recipient_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
