from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    action: str
    entity_type: str
    entity_id: str
    metadata_json: str | None
    created_at: datetime
