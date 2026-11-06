from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.db.models import AuditLog, User
from app.db.session import get_db
from app.modules.audit.schemas import AuditResponse


router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditResponse])
def list_audit_logs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AuditLog]:
    if user.role.value != "Admin":
        raise HTTPException(status_code=403, detail="Only administrators can view audit logs")
    return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc())).all())
