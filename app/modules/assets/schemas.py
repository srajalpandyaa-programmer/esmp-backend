from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssetCreate(BaseModel):
    asset_type: str = Field(min_length=2, max_length=80)
    serial_number: str | None = Field(default=None, max_length=120)


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_code: str
    asset_type: str
    serial_number: str | None
    status: str
    assigned_to: UUID | None
    created_at: datetime


class AssetAssignmentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    assigned_to: UUID | None
    action: str
    changed_by: UUID
    created_at: datetime
