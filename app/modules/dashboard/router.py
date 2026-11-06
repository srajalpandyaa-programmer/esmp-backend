from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.db.models import Asset, Approval, Notification, Ticket, TicketStatus, User
from app.db.session import get_db


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/me")
def my_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int | str]:
    ticket_query = select(func.count()).select_from(Ticket).where(Ticket.created_by == user.id)
    open_query = ticket_query.where(Ticket.status.not_in({TicketStatus.CLOSED, TicketStatus.RESOLVED}))
    approvals_query = select(func.count()).select_from(Approval).where(
        Approval.requester_id == user.id, Approval.status == "Pending"
    )
    notifications_query = select(func.count()).select_from(Notification).where(
        Notification.recipient_id == user.id, Notification.is_read.is_(False)
    )
    return {
        "role": user.role.value,
        "tickets_total": db.scalar(ticket_query) or 0,
        "tickets_open": db.scalar(open_query) or 0,
        "approvals_pending": db.scalar(approvals_query) or 0,
        "notifications_unread": db.scalar(notifications_query) or 0,
    }
