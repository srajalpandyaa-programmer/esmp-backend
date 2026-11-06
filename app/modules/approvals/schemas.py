from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApprovalCreate(BaseModel):
    request_type: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=3)


class ApprovalDecision(BaseModel):
    decision_comment: str = Field(min_length=2, max_length=1000)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_type: str
    description: str
    requester_id: UUID
    approver_id: UUID | None
    status: str
    decision_comment: str | None
    created_at: datetime
