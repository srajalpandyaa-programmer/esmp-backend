import json
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def record_audit(
    db: Session,
    *,
    actor_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | str,
    metadata: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            metadata_json=json.dumps(metadata, default=str) if metadata else None,
        )
    )
