from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.core.audit import record_audit
from app.db.models import Ticket, TicketAttachment, TicketComment, TicketStatus, TicketStatusHistory, User
from app.db.session import get_db
from app.modules.tickets.schemas import (
    TicketCreate,
    TicketResponse,
    TicketStatusHistoryResponse,
    TicketUpdate,
)
from app.modules.tickets.extra import AttachmentResponse, CommentCreate, CommentResponse


router = APIRouter(prefix="/tickets", tags=["tickets"])

ALLOWED_TRANSITIONS = {
    TicketStatus.OPEN: {TicketStatus.ASSIGNED, TicketStatus.REJECTED},
    TicketStatus.ASSIGNED: {TicketStatus.IN_PROGRESS, TicketStatus.PENDING},
    TicketStatus.IN_PROGRESS: {TicketStatus.PENDING, TicketStatus.RESOLVED},
    TicketStatus.PENDING: {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED},
    TicketStatus.RESOLVED: {TicketStatus.CLOSED, TicketStatus.IN_PROGRESS},
}


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    request: TicketCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Ticket:
    ticket = Ticket(
        ticket_number=f"TKT-{datetime.now(timezone.utc):%Y%m%d}-{str(uuid4())[:8].upper()}",
        title=request.title,
        description=request.description,
        category=request.category,
        priority=request.priority,
        status=TicketStatus.OPEN,
        created_by=user.id,
    )
    db.add(ticket)
    db.flush()
    db.add(
        TicketStatusHistory(
            ticket_id=ticket.id,
            from_status=None,
            to_status=TicketStatus.OPEN,
            changed_by=user.id,
        )
    )
    record_audit(
        db,
        actor_id=user.id,
        action="created",
        entity_type="ticket",
        entity_id=ticket.id,
        metadata={"ticket_number": ticket.ticket_number},
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=list[TicketResponse])
def list_tickets(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Ticket]:
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if user.role.value == "Employee":
        query = query.where(Ticket.created_by == user.id)
    if status_filter is not None:
        query = query.where(Ticket.status == status_filter)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    query = query.offset(offset).limit(limit)
    return list(db.scalars(query).all())


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or (user.role.value == "Employee" and ticket.created_by != user.id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/{ticket_id}/comments", response_model=CommentResponse, status_code=201)
def add_comment(
    ticket_id: UUID,
    request: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TicketComment:
    ticket = get_ticket(ticket_id, db, user)
    if request.is_internal and user.role.value == "Employee":
        raise HTTPException(status_code=403, detail="Employees cannot add internal notes")
    comment = TicketComment(
        ticket_id=ticket.id, author_id=user.id, body=request.body, is_internal=request.is_internal
    )
    db.add(comment)
    record_audit(db, actor_id=user.id, action="commented", entity_type="ticket", entity_id=ticket.id)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/{ticket_id}/comments", response_model=list[CommentResponse])
def list_comments(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TicketComment]:
    ticket = get_ticket(ticket_id, db, user)
    query = select(TicketComment).where(TicketComment.ticket_id == ticket.id)
    if user.role.value == "Employee":
        query = query.where(TicketComment.is_internal.is_(False))
    return list(db.scalars(query.order_by(TicketComment.created_at.asc())).all())


@router.post("/{ticket_id}/attachments", response_model=AttachmentResponse, status_code=201)
def add_attachment(
    ticket_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TicketAttachment:
    ticket = get_ticket(ticket_id, db, user)
    content = file.file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Attachment exceeds 10 MB limit")
    upload_dir = Path("storage") / "attachments" / str(ticket.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "attachment").name
    storage_file = upload_dir / safe_name
    storage_file.write_bytes(content)
    attachment = TicketAttachment(
        ticket_id=ticket.id,
        uploaded_by=user.id,
        filename=safe_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        storage_path=str(storage_file),
    )
    db.add(attachment)
    record_audit(db, actor_id=user.id, action="attached", entity_type="ticket", entity_id=ticket.id)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/{ticket_id}/history", response_model=list[TicketStatusHistoryResponse])
def ticket_history(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TicketStatusHistory]:
    ticket = get_ticket(ticket_id, db, user)
    return list(
        db.scalars(
            select(TicketStatusHistory)
            .where(TicketStatusHistory.ticket_id == ticket.id)
            .order_by(TicketStatusHistory.created_at.asc())
        ).all()
    )


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: UUID,
    request: TicketUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Ticket:
    ticket = get_ticket(ticket_id, db, user)
    values = request.model_dump(exclude_unset=True)
    requested_status = values.pop("status", None)
    if requested_status is not None and requested_status != ticket.status:
        if requested_status not in ALLOWED_TRANSITIONS.get(ticket.status, set()):
            raise HTTPException(status_code=422, detail="Invalid ticket status transition")
        if user.role.value == "Employee" and requested_status not in {TicketStatus.CLOSED}:
            raise HTTPException(status_code=403, detail="Employees cannot perform this transition")
        previous_status = ticket.status
        ticket.status = requested_status
        db.add(
            TicketStatusHistory(
                ticket_id=ticket.id,
                from_status=previous_status,
                to_status=requested_status,
                changed_by=user.id,
            )
        )
        record_audit(
            db,
            actor_id=user.id,
            action="status_changed",
            entity_type="ticket",
            entity_id=ticket.id,
            metadata={"from": previous_status.value, "to": requested_status.value},
        )
    if "assigned_to" in values:
        if user.role.value == "Employee":
            raise HTTPException(status_code=403, detail="Employees cannot assign tickets")
        assignee = db.get(User, values["assigned_to"])
        if assignee is None or not assignee.is_active:
            raise HTTPException(status_code=404, detail="Assignee not found or inactive")
        if ticket.assigned_to != assignee.id:
            ticket.status = TicketStatus.ASSIGNED
            record_audit(
                db,
                actor_id=user.id,
                action="assigned",
                entity_type="ticket",
                entity_id=ticket.id,
                metadata={"assigned_to": assignee.id},
            )
    for field, value in values.items():
        setattr(ticket, field, value)
    if values:
        record_audit(
            db,
            actor_id=user.id,
            action="updated",
            entity_type="ticket",
            entity_id=ticket.id,
            metadata={"fields": sorted(values)},
        )
    db.commit()
    db.refresh(ticket)
    return ticket
