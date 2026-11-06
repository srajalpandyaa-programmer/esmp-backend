from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3)
    category: str = Field(min_length=2, max_length=80)
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=3)
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    assigned_to: UUID | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_number: str
    title: str
    description: str
    category: str
    priority: TicketPriority
    status: TicketStatus
    created_by: UUID
    assigned_to: UUID | None
    created_at: datetime


class TicketStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    from_status: TicketStatus | None
    to_status: TicketStatus
    changed_by: UUID
    created_at: datetime
