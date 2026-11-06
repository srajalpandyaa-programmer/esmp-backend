from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.approvals.router import router as approvals_router
from app.modules.assets.router import router as assets_router
from app.modules.audit.router import router as audit_router
from app.modules.notifications.router import router as notifications_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.tickets.router import router as tickets_router
from app.modules.users.router import router as users_router


router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(tickets_router)
router.include_router(assets_router)
router.include_router(approvals_router)
router.include_router(notifications_router)
router.include_router(audit_router)
router.include_router(dashboard_router)
