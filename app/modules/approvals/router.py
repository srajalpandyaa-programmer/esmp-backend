from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.db.models import Approval, User
from app.db.session import get_db
from app.modules.approvals.schemas import ApprovalCreate, ApprovalDecision, ApprovalResponse


router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
def create_approval(
    request: ApprovalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Approval:
    approval = Approval(
        request_type=request.request_type,
        description=request.description,
        requester_id=user.id,
        approver_id=user.manager_id,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


@router.get("", response_model=list[ApprovalResponse])
def list_approvals(
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Approval]:
    query = select(Approval).order_by(Approval.created_at.desc())
    if user.role.value == "Employee":
        query = query.where((Approval.requester_id == user.id) | (Approval.approver_id == user.id))
    return list(db.scalars(query.offset(offset).limit(min(limit, 100))).all())


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Approval:
    approval = db.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    if user.role.value == "Employee" and user.id not in {approval.requester_id, approval.approver_id}:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.patch("/{approval_id}/approve", response_model=ApprovalResponse)
def approve(
    approval_id: UUID,
    request: ApprovalDecision,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Approval:
    return decide(approval_id, request, "Approved", db, user)


@router.patch("/{approval_id}/reject", response_model=ApprovalResponse)
def reject(
    approval_id: UUID,
    request: ApprovalDecision,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Approval:
    return decide(approval_id, request, "Rejected", db, user)


def decide(
    approval_id: UUID,
    request: ApprovalDecision,
    decision: str,
    db: Session,
    user: User,
) -> Approval:
    approval = db.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "Pending":
        raise HTTPException(status_code=409, detail="Approval has already been decided")
    if approval.approver_id not in {None, user.id} and user.role.value not in {"Admin", "Manager"}:
        raise HTTPException(status_code=403, detail="You are not the assigned approver")
    approval.approver_id = user.id
    approval.status = decision
    approval.decision_comment = request.decision_comment
    db.commit()
    db.refresh(approval)
    return approval
