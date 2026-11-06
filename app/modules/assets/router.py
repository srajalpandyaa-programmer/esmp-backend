from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.core.audit import record_audit
from app.db.models import Asset, AssetAssignmentHistory, User
from app.db.session import get_db
from app.modules.assets.schemas import (
    AssetAssignmentHistoryResponse,
    AssetCreate,
    AssetResponse,
)


router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    request: AssetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Asset:
    if user.role.value not in {"Admin", "Manager", "Support Engineer"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    asset = Asset(
        asset_code=f"AST-{str(uuid4())[:8].upper()}",
        asset_type=request.asset_type,
        serial_number=request.serial_number,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("", response_model=list[AssetResponse])
def list_assets(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Asset]:
    return list(
        db.scalars(
            select(Asset).order_by(Asset.created_at.desc()).offset(offset).limit(limit)
        ).all()
    )


@router.post("/{asset_id}/assign", response_model=AssetResponse)
def assign_asset(
    asset_id: UUID,
    assigned_to: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Asset:
    if user.role.value not in {"Admin", "Manager", "Support Engineer"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    asset = db.get(Asset, asset_id)
    recipient = db.get(User, assigned_to)
    if asset is None or recipient is None or not recipient.is_active:
        raise HTTPException(status_code=404, detail="Asset or recipient not found")
    if asset.status == "Retired":
        raise HTTPException(status_code=422, detail="Retired assets cannot be assigned")
    asset.assigned_to = recipient.id
    asset.status = "Assigned"
    db.add(
        AssetAssignmentHistory(
            asset_id=asset.id,
            assigned_to=recipient.id,
            action="assigned",
            changed_by=user.id,
        )
    )
    record_audit(
        db,
        actor_id=user.id,
        action="assigned",
        entity_type="asset",
        entity_id=asset.id,
        metadata={"assigned_to": recipient.id},
    )
    db.commit()
    db.refresh(asset)
    return asset


@router.post("/{asset_id}/return", response_model=AssetResponse)
def return_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Asset:
    if user.role.value not in {"Admin", "Manager", "Support Engineer"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.assigned_to is None:
        raise HTTPException(status_code=409, detail="Asset is not assigned")
    previous_user = asset.assigned_to
    asset.assigned_to = None
    asset.status = "Available"
    db.add(
        AssetAssignmentHistory(
            asset_id=asset.id,
            assigned_to=None,
            action="returned",
            changed_by=user.id,
        )
    )
    record_audit(
        db,
        actor_id=user.id,
        action="returned",
        entity_type="asset",
        entity_id=asset.id,
        metadata={"previous_assigned_to": previous_user},
    )
    db.commit()
    db.refresh(asset)
    return asset


@router.patch("/{asset_id}/retire", response_model=AssetResponse)
def retire_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Asset:
    if user.role.value not in {"Admin", "Manager"}:
        raise HTTPException(status_code=403, detail="Only administrators or managers can retire assets")
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset.assigned_to = None
    asset.status = "Retired"
    record_audit(
        db,
        actor_id=user.id,
        action="retired",
        entity_type="asset",
        entity_id=asset.id,
    )
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{asset_id}/history", response_model=list[AssetAssignmentHistoryResponse])
def asset_history(
    asset_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AssetAssignmentHistory]:
    if db.get(Asset, asset_id) is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return list(
        db.scalars(
            select(AssetAssignmentHistory)
            .where(AssetAssignmentHistory.asset_id == asset_id)
            .order_by(AssetAssignmentHistory.created_at.asc())
        ).all()
    )
